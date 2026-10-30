"""
AI Matching Engine for Lost and Found System
Uses:
  - Color histogram comparison for image similarity
  - TF-IDF + cosine similarity for text matching
  - Weighted scoring combining multiple features
"""
import os
import math
import re
from typing import Optional
import numpy as np
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import database as db


# ── Text helpers ─────────────────────────────────────────────────────────────

def _preprocess_text(text: str) -> str:
    """Lowercase, remove punctuation, collapse spaces."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compute_text_similarity(text_a: str, text_b: str) -> float:
    """TF-IDF cosine similarity between two text strings (0–1)."""
    if not text_a.strip() or not text_b.strip():
        return 0.0
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        matrix = vec.fit_transform([_preprocess_text(text_a), _preprocess_text(text_b)])
        score = cosine_similarity(matrix[0], matrix[1])[0][0]
        return float(np.clip(score, 0.0, 1.0))
    except Exception:
        return 0.0


def compute_keyword_overlap(text_a: str, text_b: str) -> float:
    """Simple word-overlap Jaccard coefficient."""
    words_a = set(_preprocess_text(text_a).split())
    words_b = set(_preprocess_text(text_b).split())
    # remove very common stop words
    stops = {"a","an","the","is","it","in","on","at","to","for","of","and","or","with","my","i"}
    words_a -= stops
    words_b -= stops
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def category_match(cat_a: str, cat_b: str) -> float:
    return 1.0 if cat_a.lower() == cat_b.lower() else 0.0


def color_text_match(color_a: str, color_b: str) -> float:
    if not color_a or not color_b:
        return 0.5          # unknown → neutral
    ca = _preprocess_text(color_a)
    cb = _preprocess_text(color_b)
    if ca == cb:
        return 1.0
    # partial word overlap
    wa = set(ca.split())
    wb = set(cb.split())
    if wa & wb:
        return 0.6
    return 0.0


def brand_match(brand_a: str, brand_b: str) -> float:
    if not brand_a or not brand_b:
        return 0.5
    return 1.0 if brand_a.lower().strip() == brand_b.lower().strip() else 0.0


# ── Image helpers ─────────────────────────────────────────────────────────────

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")


def _load_image(path: str) -> Optional[Image.Image]:
    full = os.path.join(UPLOADS_DIR, os.path.basename(path)) if not os.path.isabs(path) else path
    try:
        return Image.open(full).convert("RGB")
    except Exception:
        return None


def _color_histogram(img: Image.Image, bins: int = 32) -> np.ndarray:
    """Compute a flattened RGB histogram (normalised)."""
    hist = []
    for ch in range(3):
        channel = np.array(img)[:, :, ch]
        h, _ = np.histogram(channel, bins=bins, range=(0, 256))
        hist.append(h)
    hist_arr = np.concatenate(hist).astype(float)
    norm = hist_arr.sum()
    return hist_arr / norm if norm > 0 else hist_arr


def compute_image_similarity(path_a: str, path_b: str) -> float:
    """Histogram intersection similarity between two images (0–1)."""
    if not path_a or not path_b:
        return 0.5          # unknown → neutral
    img_a = _load_image(path_a)
    img_b = _load_image(path_b)
    if img_a is None or img_b is None:
        return 0.5
    # Resize to same thumbnail for speed
    size = (128, 128)
    img_a = img_a.resize(size, Image.LANCZOS)
    img_b = img_b.resize(size, Image.LANCZOS)
    ha = _color_histogram(img_a)
    hb = _color_histogram(img_b)
    # Histogram intersection
    intersection = np.minimum(ha, hb).sum()
    return float(np.clip(intersection, 0.0, 1.0))


# ── Master scoring ────────────────────────────────────────────────────────────

WEIGHTS = {
    "category":    0.20,
    "text_sim":    0.30,
    "keyword":     0.15,
    "color":       0.10,
    "brand":       0.10,
    "image":       0.15,
}


def score_pair(lost: dict, found: dict) -> float:
    """
    Compute an overall match score [0, 1] between a lost item and a found item.
    """
    cat_score   = category_match(lost.get("category",""), found.get("category",""))

    # Build combined text from title + description
    text_lost  = f"{lost.get('title','')} {lost.get('description','')}"
    text_found = f"{found.get('title','')} {found.get('description','')}"
    text_score  = compute_text_similarity(text_lost, text_found)
    kw_score    = compute_keyword_overlap(text_lost, text_found)

    color_score = color_text_match(lost.get("color",""), found.get("color",""))
    brand_score = brand_match(lost.get("brand",""), found.get("brand",""))
    img_score   = compute_image_similarity(lost.get("image_path",""), found.get("image_path",""))

    total = (
        WEIGHTS["category"] * cat_score +
        WEIGHTS["text_sim"] * text_score +
        WEIGHTS["keyword"]  * kw_score +
        WEIGHTS["color"]    * color_score +
        WEIGHTS["brand"]    * brand_score +
        WEIGHTS["image"]    * img_score
    )
    return round(float(np.clip(total, 0.0, 1.0)), 4)


# ── Public API ────────────────────────────────────────────────────────────────

MATCH_THRESHOLD = 0.30     # minimum score to record a match


def run_matching_for_item(item_id: int) -> list[dict]:
    """
    Given a newly added item, compare it against all active items of the
    opposite type and store matches above threshold.
    Returns sorted list of match result dicts.
    """
    item = db.get_item(item_id)
    if not item:
        return []

    opposite = "found" if item["type"] == "lost" else "lost"
    candidates = db.get_all_items(item_type=opposite, status="active")

    results = []
    for candidate in candidates:
        if item["type"] == "lost":
            lost_item, found_item = item, candidate
        else:
            lost_item, found_item = candidate, item

        score = score_pair(lost_item, found_item)
        if score >= MATCH_THRESHOLD:
            match_id = db.insert_match(lost_item["id"], found_item["id"], score)
            if match_id:
                db.insert_notification(
                    item_id=item_id,
                    match_id=match_id,
                    message=(
                        f"Potential match found! "
                        f"Lost: '{lost_item['title']}' ↔ Found: '{found_item['title']}' "
                        f"(score: {score*100:.0f}%)"
                    )
                )
            results.append({
                "match_id": match_id,
                "lost_id":  lost_item["id"],
                "found_id": found_item["id"],
                "lost_title":  lost_item["title"],
                "found_title": found_item["title"],
                "score": score,
                "score_pct": f"{score*100:.0f}%",
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def get_top_matches(item_id: int, limit: int = 5) -> list[dict]:
    """Return existing matches for an item, sorted by score."""
    matches = db.get_matches_for_item(item_id)
    return sorted(matches, key=lambda x: x["score"], reverse=True)[:limit]
