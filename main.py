"""
FastAPI main application — AI Lost and Found System
"""
import os
import uuid
import shutil
from typing import Optional

from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import database as db
import matcher

# ── App setup ────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(title="AI Lost & Found", version="1.0.0")
app.mount("/static",  StaticFiles(directory=os.path.join(BASE_DIR, "static")),  name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR),                        name="uploads")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Initialise DB on startup
db.init_db()


# ── Helpers ───────────────────────────────────────────────────────────────────

def save_upload(file: UploadFile) -> Optional[str]:
    if not file or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return None
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOADS_DIR, filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return filename


def score_badge(score: float) -> str:
    pct = int(score * 100)
    if pct >= 70:
        return "badge-high"
    if pct >= 45:
        return "badge-medium"
    return "badge-low"


# Inject helpers into Jinja2
templates.env.globals["score_badge"] = score_badge
templates.env.globals["int"] = int


# ── Helper: build TemplateResponse (compatible with all Starlette versions) ──

def render(request: Request, template_name: str, context: dict = None):
    ctx = context or {}
    ctx["request"] = request
    return templates.TemplateResponse(request=request, name=template_name, context=ctx)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    stats        = db.get_stats()
    recent_lost  = db.get_all_items("lost")[:4]
    recent_found = db.get_all_items("found")[:4]
    notifications = db.get_notifications(5)
    unread = sum(1 for n in notifications if not n["is_read"])
    return render(request, "index.html", {
        "stats": stats,
        "recent_lost": recent_lost,
        "recent_found": recent_found,
        "notifications": notifications,
        "unread": unread,
    })


# ── Report ────────────────────────────────────────────────────────────────────

@app.get("/report", response_class=HTMLResponse)
async def report_form(request: Request, type: str = "lost"):
    return render(request, "report.html", {
        "item_type": type,
        "categories": CATEGORIES,
    })


@app.post("/report", response_class=HTMLResponse)
async def report_submit(
    request: Request,
    type: str          = Form(...),
    title: str         = Form(...),
    description: str   = Form(...),
    category: str      = Form(...),
    location: str      = Form(...),
    date_occurred: str = Form(...),
    contact_name: str  = Form(...),
    contact_email: str = Form(...),
    contact_phone: str = Form(""),
    color: str         = Form(""),
    brand: str         = Form(""),
    image: UploadFile  = File(None),
):
    image_path = save_upload(image)
    data = {
        "type": type, "title": title, "description": description,
        "category": category, "location": location, "date_occurred": date_occurred,
        "contact_name": contact_name, "contact_email": contact_email,
        "contact_phone": contact_phone, "image_path": image_path,
        "color": color, "brand": brand,
    }
    item_id = db.insert_item(data)
    matches = matcher.run_matching_for_item(item_id)
    return RedirectResponse(url=f"/item/{item_id}?new=1&matches={len(matches)}", status_code=303)


# ── Browse ────────────────────────────────────────────────────────────────────

@app.get("/browse", response_class=HTMLResponse)
async def browse(
    request: Request,
    type: str     = "lost",
    category: str = "",
    search: str   = "",
):
    items = db.get_all_items(item_type=type if type in ("lost", "found") else None)
    if category:
        items = [i for i in items if i["category"].lower() == category.lower()]
    if search:
        kw = search.lower()
        items = [i for i in items if kw in i["title"].lower() or kw in i["description"].lower()]
    return render(request, "browse.html", {
        "items": items,
        "current_type": type,
        "current_category": category,
        "search": search,
        "categories": CATEGORIES,
    })


# ── Item detail ───────────────────────────────────────────────────────────────

@app.get("/item/{item_id}", response_class=HTMLResponse)
async def item_detail(request: Request, item_id: int, new: int = 0, matches: int = 0):
    item = db.get_item(item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    item_matches = matcher.get_top_matches(item_id, limit=6)
    return render(request, "item_detail.html", {
        "item": item,
        "matches": item_matches,
        "is_new": new == 1,
        "match_count": matches,
        "score_badge": score_badge,
    })


# ── Matches dashboard ─────────────────────────────────────────────────────────

@app.get("/matches", response_class=HTMLResponse)
async def matches_dashboard(request: Request):
    all_matches = db.get_all_matches(limit=50)
    return render(request, "matches.html", {
        "matches": all_matches,
        "score_badge": score_badge,
    })


# ── Confirm / Reject match ────────────────────────────────────────────────────

@app.post("/match/{match_id}/confirm")
async def confirm_match(match_id: int):
    db.update_match_status(match_id, "confirmed")
    return JSONResponse({"status": "confirmed"})


@app.post("/match/{match_id}/reject")
async def reject_match(match_id: int):
    db.update_match_status(match_id, "rejected")
    return JSONResponse({"status": "rejected"})


# ── Mark item resolved ────────────────────────────────────────────────────────

@app.post("/item/{item_id}/resolve")
async def resolve_item(item_id: int):
    db.update_item_status(item_id, "resolved")
    return JSONResponse({"status": "resolved"})


# ── Delete item ───────────────────────────────────────────────────────────────

@app.post("/item/{item_id}/delete")
async def delete_item(item_id: int):
    item = db.get_item(item_id)
    if item and item.get("image_path"):
        img = os.path.join(UPLOADS_DIR, item["image_path"])
        if os.path.exists(img):
            os.remove(img)
    db.delete_item(item_id)
    return JSONResponse({"status": "deleted"})


# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
async def api_stats():
    return db.get_stats()


@app.get("/api/items")
async def api_items(type: str = None, status: str = "active"):
    return db.get_all_items(item_type=type, status=status)


@app.get("/api/matches")
async def api_matches():
    return db.get_all_matches()


@app.get("/api/notifications")
async def api_notifications():
    notes = db.get_notifications()
    db.mark_notifications_read()
    return notes


@app.post("/api/rematch/{item_id}")
async def api_rematch(item_id: int):
    results = matcher.run_matching_for_item(item_id)
    return {"matches": results, "count": len(results)}


# ── Categories ────────────────────────────────────────────────────────────────

CATEGORIES = [
    "Electronics", "Wallet / Purse", "Keys", "Bag / Backpack",
    "Clothing", "Jewelry / Accessories", "Documents / ID",
    "Pet", "Bicycle / Vehicle", "Books / Stationery",
    "Sports Equipment", "Toys", "Other",
]
