# 🔍 AI-Based Lost and Found Object Matching System

A full-stack web application that uses AI to automatically match lost items with found items.

## 🚀 Quick Start

```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Seed demo data (first time only)
python seed.py

# Start the server
run.bat
# OR
python -m uvicorn main:app --reload --port 8000
```

Open your browser at **http://localhost:8000**

---

## 🧠 How AI Matching Works

When you report a lost or found item, the AI engine immediately compares it against all active items of the opposite type using:

| Feature | Weight | Method |
|---------|--------|--------|
| Category | 20% | Exact match |
| Text Description | 30% | TF-IDF + Cosine Similarity |
| Keywords | 15% | Jaccard word overlap |
| Image | 15% | RGB histogram intersection |
| Color | 10% | Word-level match |
| Brand | 10% | Exact match |

Matches above **30% score** are automatically recorded and a notification is generated.

---

## 📁 Project Structure

```
ai lost and found iteam/
├── main.py          # FastAPI app + all routes
├── database.py      # SQLite database layer
├── matcher.py       # AI matching engine
├── seed.py          # Demo data seeder
├── run.bat          # Windows launcher
├── requirements.txt
├── data/
│   └── lost_found.db    # SQLite database
├── uploads/             # User-uploaded images
├── static/
│   ├── css/style.css    # Full UI stylesheet
│   └── js/app.js        # Frontend JavaScript
└── templates/
    ├── base.html         # Shared layout + sidebar
    ├── index.html        # Dashboard
    ├── report.html       # Report lost/found form
    ├── browse.html       # Browse & search items
    ├── item_detail.html  # Item detail + matches
    └── matches.html      # AI matches dashboard
```

---

## 🌐 Pages

| URL | Description |
|-----|-------------|
| `/` | Dashboard with stats & recent items |
| `/report?type=lost` | Report a lost item |
| `/report?type=found` | Report a found item |
| `/browse?type=lost` | Browse lost items |
| `/browse?type=found` | Browse found items |
| `/item/{id}` | Item detail + AI matches |
| `/matches` | All AI matches dashboard |

## 🔌 API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/stats` | System statistics |
| GET | `/api/items` | List all items |
| GET | `/api/matches` | List all matches |
| GET | `/api/notifications` | Get notifications |
| POST | `/api/rematch/{id}` | Re-run AI matching |
| POST | `/match/{id}/confirm` | Confirm a match |
| POST | `/match/{id}/reject` | Reject a match |
| POST | `/item/{id}/resolve` | Mark item resolved |
| POST | `/item/{id}/delete` | Delete item |

---

## ✨ Features

- **AI Matching** — Automatically compares text, images, color, brand, category
- **Real-time notifications** — Bell icon shows new matches
- **Image upload** — Drag & drop photo upload
- **Search & filter** — Filter by category, type, keywords
- **Match management** — Confirm or reject AI suggestions
- **Responsive UI** — Works on mobile, tablet, desktop
- **Auto-refresh stats** — Dashboard updates every 30 seconds
