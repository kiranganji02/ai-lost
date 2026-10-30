"""
Seed the database with realistic demo data so you can see the system in action immediately.
Run once: python seed.py
"""
import database as db
import matcher

db.init_db()

ITEMS = [
    # Lost items
    {
        "type": "lost", "title": "Black iPhone 15 Pro",
        "description": "Lost my black iPhone 15 Pro with a cracked screen protector. Has a black leather case with a card holder at the back. Contains important family photos.",
        "category": "Electronics", "location": "Central Mall, Food Court, 3rd Floor",
        "date_occurred": "2026-10-18", "contact_name": "Arjun Sharma",
        "contact_email": "arjun@example.com", "contact_phone": "+91-9876543210",
        "image_path": None, "color": "Black", "brand": "Apple"
    },
    {
        "type": "lost", "title": "Brown Leather Wallet",
        "description": "Brown genuine leather bi-fold wallet. Contains Aadhar card, PAN card, debit cards and approximately 2000 rupees in cash. Has 'AS' initials embossed on the inside.",
        "category": "Wallet / Purse", "location": "City Bus Stop, Near Railway Station",
        "date_occurred": "2026-10-20", "contact_name": "Priya Mehta",
        "contact_email": "priya@example.com", "contact_phone": "+91-8765432109",
        "image_path": None, "color": "Brown", "brand": ""
    },
    {
        "type": "lost", "title": "Blue Nike Backpack",
        "description": "Medium-sized Nike backpack in navy blue. Contains a laptop, charger, and notebooks. Has a small red keychain attached to the zipper. Lost while commuting.",
        "category": "Bag / Backpack", "location": "Metro Station - MG Road Platform 2",
        "date_occurred": "2026-10-21", "contact_name": "Rahul Kumar",
        "contact_email": "rahul@example.com", "contact_phone": "",
        "image_path": None, "color": "Blue", "brand": "Nike"
    },
    {
        "type": "lost", "title": "Golden Necklace with Pendant",
        "description": "22-carat gold necklace with a small lotus flower pendant. Has sentimental value, was a wedding gift. Chain length approximately 18 inches.",
        "category": "Jewelry / Accessories", "location": "Lalbagh Botanical Garden, Near Rose Garden",
        "date_occurred": "2026-10-19", "contact_name": "Sunita Reddy",
        "contact_email": "sunita@example.com", "contact_phone": "+91-7654321098",
        "image_path": None, "color": "Gold", "brand": ""
    },
    {
        "type": "lost", "title": "Car Keys — Honda City",
        "description": "Honda City car keys with a black remote fob. Has a small Ganesha keychain attached. Lost after visiting the supermarket.",
        "category": "Keys", "location": "Big Bazaar Supermarket, Koramangala",
        "date_occurred": "2026-10-22", "contact_name": "Vikram Singh",
        "contact_email": "vikram@example.com", "contact_phone": "+91-9988776655",
        "image_path": None, "color": "Black", "brand": "Honda"
    },
    # Found items
    {
        "type": "found", "title": "Found Black Apple iPhone",
        "description": "Found a black iPhone with a cracked screen protector near the food court. The phone has a leather case. Submitted to security desk.",
        "category": "Electronics", "location": "Central Mall, Security Desk, Ground Floor",
        "date_occurred": "2026-10-18", "contact_name": "Mall Security",
        "contact_email": "security@centralmall.com", "contact_phone": "+91-8001234567",
        "image_path": None, "color": "Black", "brand": "Apple"
    },
    {
        "type": "found", "title": "Leather Wallet Found on Bus",
        "description": "Found a brown leather wallet on Bus No. 45B. Contains ID cards and cash. Handed over to the bus conductor who asked me to post here.",
        "category": "Wallet / Purse", "location": "Bus Route 45B, Near Railway Station Area",
        "date_occurred": "2026-10-20", "contact_name": "Deepak Nair",
        "contact_email": "deepak@example.com", "contact_phone": "",
        "image_path": None, "color": "Brown", "brand": ""
    },
    {
        "type": "found", "title": "Blue Backpack Left at Metro",
        "description": "Found a navy blue backpack at MG Road metro station. Contains a laptop and study material. Kept safely with station master.",
        "category": "Bag / Backpack", "location": "MG Road Metro Station, Station Master Office",
        "date_occurred": "2026-10-21", "contact_name": "Station Master",
        "contact_email": "mgroad.metro@example.com", "contact_phone": "+91-9001122334",
        "image_path": None, "color": "Blue", "brand": ""
    },
    {
        "type": "found", "title": "Set of Car Keys Found",
        "description": "Found a car remote key with a religious keychain in the parking lot. Appears to be for a Honda vehicle. Left at customer service.",
        "category": "Keys", "location": "Big Bazaar Parking Lot, Koramangala",
        "date_occurred": "2026-10-22", "contact_name": "Customer Service",
        "contact_email": "cs@bigbazaar.com", "contact_phone": "",
        "image_path": None, "color": "Black", "brand": "Honda"
    },
    {
        "type": "found", "title": "Passport and Documents",
        "description": "Found a passport along with some bank documents in a brown envelope near the airport departure gate. Owner name visible on passport.",
        "category": "Documents / ID", "location": "Kempegowda International Airport, Terminal 1",
        "date_occurred": "2026-10-17", "contact_name": "Airport Authority",
        "contact_email": "lostfound@blrairport.com", "contact_phone": "+91-8022001122",
        "image_path": None, "color": "", "brand": ""
    },
]


def seed():
    print("Seeding database...")
    ids = []
    for item_data in ITEMS:
        iid = db.insert_item(item_data)
        ids.append(iid)
        print(f"  Added [{item_data['type']}] id={iid}: {item_data['title']}")

    print("\nRunning AI matching for all items...")
    for iid in ids:
        matches = matcher.run_matching_for_item(iid)
        if matches:
            print(f"  Item {iid}: {len(matches)} match(es) found")
            for m in matches[:2]:
                print(f"    -> Lost '{m['lost_title']}' <-> Found '{m['found_title']}' ({m['score_pct']})")

    stats = db.get_stats()
    print(f"\nDatabase seeded! Stats: {stats}")


if __name__ == "__main__":
    seed()
