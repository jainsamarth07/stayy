#!/usr/bin/env python3
"""
StayNest — Large-scale seed script (50k properties)
====================================================
Generates realistic test data directly into PostgreSQL for load/E2E testing.

Usage:
  pip install psycopg2-binary argon2-cffi faker
  python seed_large.py                          # defaults
  python seed_large.py --properties 50000       # custom count
  python seed_large.py --db-url "postgresql://staynest:staynest_secret@localhost:5432/staynest"

What it creates:
  - 1 admin user
  - 500 host users (with host_profiles & memberships)
  - 5,000 guest users
  - 50,000 properties (with 2-5 images each from picsum.photos)
  - ~100,000 bookings (mix of completed, confirmed, pending, cancelled)
  - ~40,000 reviews (on completed bookings)
  - ~10,000 conversations with ~30,000 messages

All users share password: TestPass123!
Admin email: admin@staynest.com
"""

import argparse
import io
import math
import random
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Try to import optional deps; guide user if missing
# ---------------------------------------------------------------------------
try:
    from argon2 import PasswordHasher
except ImportError:
    print("❌ Missing dependency: pip install argon2-cffi")
    sys.exit(1)

try:
    from faker import Faker
except ImportError:
    print("❌ Missing dependency: pip install faker")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SHARED_PASSWORD = "TestPass123!"
ph = PasswordHasher()
HASHED_PASSWORD = ph.hash(SHARED_PASSWORD)

fake = Faker()
Faker.seed(42)
random.seed(42)

UTC = timezone.utc
NOW = datetime.now(UTC)

# Property data pools
CITIES = [
    ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    ("Delhi", "Delhi", 28.7041, 77.1025),
    ("Bangalore", "Karnataka", 12.9716, 77.5946),
    ("Hyderabad", "Telangana", 17.3850, 78.4867),
    ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    ("Kolkata", "West Bengal", 22.5726, 88.3639),
    ("Pune", "Maharashtra", 18.5204, 73.8567),
    ("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    ("Goa", "Goa", 15.2993, 74.1240),
    ("Kochi", "Kerala", 9.9312, 76.2673),
    ("Udaipur", "Rajasthan", 24.5854, 73.7125),
    ("Shimla", "Himachal Pradesh", 31.1048, 77.1734),
    ("Manali", "Himachal Pradesh", 32.2396, 77.1887),
    ("Rishikesh", "Uttarakhand", 30.0869, 78.2676),
    ("Varanasi", "Uttar Pradesh", 25.3176, 83.0064),
    ("Mysore", "Karnataka", 12.2958, 76.6394),
    ("Ooty", "Tamil Nadu", 11.4102, 76.6950),
    ("Darjeeling", "West Bengal", 27.0410, 88.2663),
    ("Amritsar", "Punjab", 31.6340, 74.8723),
    ("Jodhpur", "Rajasthan", 26.2389, 73.0243),
    ("Coorg", "Karnataka", 12.3375, 75.8069),
    ("Munnar", "Kerala", 10.0889, 77.0595),
    ("Pondicherry", "Tamil Nadu", 11.9416, 79.8083),
    ("Chandigarh", "Chandigarh", 30.7333, 76.7794),
    ("Indore", "Madhya Pradesh", 22.7196, 75.8577),
    ("Agra", "Uttar Pradesh", 27.1767, 78.0081),
    ("Jaisalmer", "Rajasthan", 26.9157, 70.9083),
    ("Alleppey", "Kerala", 9.4981, 76.3388),
    ("Dehradun", "Uttarakhand", 30.3165, 78.0322),
    ("Gangtok", "Sikkim", 27.3389, 88.6065),
    ("Leh", "Ladakh", 34.1526, 77.5771),
    ("Srinagar", "Jammu & Kashmir", 34.0837, 74.7973),
    ("Thiruvananthapuram", "Kerala", 8.5241, 76.9366),
    ("Visakhapatnam", "Andhra Pradesh", 17.6868, 83.2185),
    ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
    ("Nashik", "Maharashtra", 20.0063, 73.7900),
    ("Coimbatore", "Tamil Nadu", 11.0168, 76.9558),
    ("Nagpur", "Maharashtra", 21.1458, 79.0882),
]

PROPERTY_TYPES = [
    "Cozy", "Modern", "Luxury", "Rustic", "Charming", "Elegant", "Spacious",
    "Sunny", "Stylish", "Tranquil", "Urban", "Downtown", "Beachfront",
    "Mountain", "Lakeside", "Historic", "Contemporary", "Boutique", "Designer",
    "Penthouse",
]

PROPERTY_NOUNS = [
    "Apartment", "Condo", "Loft", "Studio", "Townhouse", "Villa", "Suite",
    "Bungalow", "Cottage", "Retreat", "Flat", "Penthouse", "House", "Cabin",
    "Hideaway",
]

AMENITIES_POOL = [
    "WiFi", "Kitchen", "Air Conditioning", "Heating", "Washer", "Dryer",
    "Free Parking", "Pool", "Hot Tub", "Gym", "TV", "Workspace",
    "Coffee Maker", "Dishwasher", "BBQ Grill", "Patio", "Balcony",
    "Fireplace", "EV Charger", "Pet Friendly", "Elevator", "Doorman",
    "Self Check-in", "Smoke Alarm", "First Aid Kit",
]

REVIEW_COMMENTS = [
    "Amazing stay! The place was exactly as described and the host was very responsive.",
    "Great location, very clean and comfortable. Would definitely book again.",
    "Perfect for a weekend getaway. The amenities were top notch.",
    "Had a wonderful time. The neighborhood was lovely and felt very safe.",
    "Beautiful space with stunning views. Highly recommend!",
    "Very cozy and well-maintained. The kitchen had everything we needed.",
    "Fantastic host! Check-in was smooth and the place was spotless.",
    "Good value for the price. Central location made it easy to explore.",
    "The apartment exceeded our expectations. So much space!",
    "Loved the decor and attention to detail. Will be back for sure.",
    "Nice place but a bit noisy at night due to street traffic.",
    "Clean and functional. Nothing fancy but gets the job done.",
    "The photos were accurate. No surprises, which is always appreciated.",
    "Comfortable beds and great water pressure. The little things matter!",
    "Host was super helpful with restaurant recommendations.",
    "Ideal for families. The kids loved the pool area.",
    "Quiet neighborhood, perfect for remote work. Fast WiFi.",
    "Stylish interior, felt like staying in a design magazine.",
    "A bit hard to find parking but otherwise excellent.",
    "The balcony view was incredible, especially at sunset.",
]

# Picsum photos for property images — deterministic by seed ID
def picsum_url(seed: int, width: int = 800, height: int = 600) -> str:
    return f"https://picsum.photos/seed/{seed}/{width}/{height}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def gen_uuid() -> str:
    return str(uuid.uuid4())


def random_date_between(start: datetime, end: datetime) -> datetime:
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def progress(current: int, total: int, label: str):
    pct = current / total * 100
    bar_len = 40
    filled = int(bar_len * current / total)
    bar = "█" * filled + "░" * (bar_len - filled)
    print(f"\r  {label}: |{bar}| {pct:5.1f}% ({current:,}/{total:,})", end="", flush=True)
    if current == total:
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Seed StayNest with large-scale test data")
    parser.add_argument(
        "--db-url",
        default="postgresql://staynest:staynest_secret@localhost:5432/staynest",
        help="PostgreSQL connection URL (psycopg2 format, not asyncpg)",
    )
    parser.add_argument("--properties", type=int, default=50_000, help="Number of properties")
    parser.add_argument("--hosts", type=int, default=500, help="Number of host users")
    parser.add_argument("--guests", type=int, default=5_000, help="Number of guest users")
    parser.add_argument("--bookings", type=int, default=100_000, help="Number of bookings")
    parser.add_argument("--reviews-pct", type=float, default=0.4, help="Fraction of completed bookings that get reviews")
    parser.add_argument("--conversations", type=int, default=10_000, help="Number of conversations")
    parser.add_argument("--reset", action="store_true", help="Truncate all tables before seeding")
    args = parser.parse_args()

    print("=" * 60)
    print("  StayNest — Large-Scale Seed Script")
    print("=" * 60)
    print(f"  Properties:     {args.properties:,}")
    print(f"  Hosts:          {args.hosts:,}")
    print(f"  Guests:         {args.guests:,}")
    print(f"  Bookings:       {args.bookings:,}")
    print(f"  Conversations:  {args.conversations:,}")
    print(f"  DB:             {args.db_url.split('@')[1] if '@' in args.db_url else args.db_url}")
    print()

    t_start = time.time()

    conn = psycopg2.connect(args.db_url)
    conn.autocommit = False
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # Optional: reset
    # ------------------------------------------------------------------
    if args.reset:
        print("⚠️  Truncating all tables...")
        cur.execute("""
            TRUNCATE reviews, bookings, messages, conversations,
                     memberships, property_images, hourly_booking_configs,
                     properties, host_profiles, users
            CASCADE
        """)
        conn.commit()
        print("  Done.\n")

    # ------------------------------------------------------------------
    # 1. Users
    # ------------------------------------------------------------------
    print("👤 Creating users...")

    admin_id = gen_uuid()
    all_users = []  # (id, email, full_name, role)

    # Admin
    all_users.append((admin_id, "admin@staynest.com", "Admin User", "admin"))

    # Hosts
    host_ids = []
    for i in range(args.hosts):
        uid = gen_uuid()
        host_ids.append(uid)
        all_users.append((uid, f"host{i+1}@staynest.com", fake.name(), "host"))

    # Guests
    guest_ids = []
    for i in range(args.guests):
        uid = gen_uuid()
        guest_ids.append(uid)
        all_users.append((uid, f"guest{i+1}@staynest.com", fake.name(), "user"))

    # Bulk insert users via COPY
    buf = io.StringIO()
    for uid, email, name, role in all_users:
        phone = fake.phone_number()[:20]
        created = random_date_between(NOW - timedelta(days=730), NOW - timedelta(days=30))
        line = "\t".join([
            uid, email, HASHED_PASSWORD, name, phone, role,
            "t",  # is_active
            created.isoformat(),
            created.isoformat(),
            "",  # password_changed_at (NULL)
        ])
        buf.write(line + "\n")
    buf.seek(0)
    cur.copy_from(buf, "users", columns=[
        "id", "email", "hashed_password", "full_name", "phone", "role",
        "is_active", "created_at", "updated_at", "password_changed_at",
    ], null="")
    conn.commit()
    print(f"  ✅ {len(all_users):,} users created (1 admin, {args.hosts:,} hosts, {args.guests:,} guests)")

    # ------------------------------------------------------------------
    # 2. Host Profiles
    # ------------------------------------------------------------------
    print("🏠 Creating host profiles...")
    host_profile_ids = {}  # user_id -> profile_id

    buf = io.StringIO()
    for uid in host_ids:
        pid = gen_uuid()
        host_profile_ids[uid] = pid
        biz = fake.company()
        bio = fake.catch_phrase()
        created = NOW - timedelta(days=random.randint(30, 700))
        line = "\t".join([
            pid, uid, biz, bio, random.choice(["t", "f"]),
            random.choice(["t", "f"]),  # is_verified
            str(round(random.uniform(3.5, 5.0), 1)),  # avg_rating
            str(random.randint(0, 200)),  # total_reviews
            created.isoformat(),
        ])
        buf.write(line + "\n")
    buf.seek(0)
    cur.copy_from(buf, "host_profiles", columns=[
        "id", "user_id", "business_name", "bio", "phone_visible",
        "is_verified", "avg_rating", "total_reviews", "created_at",
    ])
    conn.commit()
    print(f"  ✅ {len(host_ids):,} host profiles created")

    # ------------------------------------------------------------------
    # 3. Memberships (one per host)
    # ------------------------------------------------------------------
    print("💎 Creating memberships...")
    plans = [
        ("basic", "2499.00", 5),
        ("pro", "6499.00", 25),
        ("premium", "16499.00", 999999),
    ]
    buf = io.StringIO()
    for uid in host_ids:
        plan, amount, max_list = random.choice(plans)
        start = NOW - timedelta(days=random.randint(1, 365))
        end = start + timedelta(days=365)
        status = "active" if end > NOW else "expired"
        line = "\t".join([
            gen_uuid(),
            host_profile_ids[uid],
            plan,
            start.isoformat(),
            end.isoformat(),
            status,
            "t",  # auto_renew
            f"pay_{uuid.uuid4().hex[:12]}",
            amount,
            str(max_list),
            NOW.isoformat(),
            NOW.isoformat(),
        ])
        buf.write(line + "\n")
    buf.seek(0)
    cur.copy_from(buf, "memberships", columns=[
        "id", "host_id", "plan_type", "start_date", "end_date", "status",
        "auto_renew", "payment_ref", "amount", "max_listings",
        "created_at", "updated_at",
    ])
    conn.commit()
    print(f"  ✅ {len(host_ids):,} memberships created")

    # ------------------------------------------------------------------
    # 4. Properties
    # ------------------------------------------------------------------
    print(f"🏡 Creating {args.properties:,} properties...")

    property_ids = []
    property_host_map = {}  # property_id -> host_id
    property_price_map = {}  # property_id -> price_per_night

    BATCH = 5000
    num_batches = math.ceil(args.properties / BATCH)
    img_seed_counter = 1000  # starting seed for picsum

    for batch_idx in range(num_batches):
        start_i = batch_idx * BATCH
        end_i = min(start_i + BATCH, args.properties)

        prop_buf = io.StringIO()
        img_buf = io.StringIO()

        for i in range(start_i, end_i):
            pid = gen_uuid()
            host_id = random.choice(host_ids)
            city_name, state, lat, lng = random.choice(CITIES)
            prop_type = random.choice(PROPERTY_TYPES)
            noun = random.choice(PROPERTY_NOUNS)
            title = f"{prop_type} {noun} in {city_name}"
            desc = (
                f"Welcome to this {prop_type.lower()} {noun.lower()} in the heart of {city_name}, {state}. "
                f"{fake.paragraph(nb_sentences=3)} "
                f"Perfect for travelers looking for a comfortable stay."
            )
            address = f"{random.randint(1, 999)}, {fake.street_name()}, {city_name}, {state}, India"
            lat_jitter = lat + random.uniform(-0.05, 0.05)
            lng_jitter = lng + random.uniform(-0.05, 0.05)
            price = round(random.uniform(800, 25000), 2)
            max_guests = random.randint(1, 12)
            amenities_list = random.sample(AMENITIES_POOL, random.randint(3, 12))
            import json as _json
            amenities_json = _json.dumps(amenities_list)
            created = random_date_between(NOW - timedelta(days=700), NOW - timedelta(days=5))

            property_ids.append(pid)
            property_host_map[pid] = host_id
            property_price_map[pid] = price

            prop_line = "\t".join([
                pid, host_id, title, desc, city_name, address,
                f"{lat_jitter:.6f}", f"{lng_jitter:.6f}",
                f"{price:.2f}", str(max_guests),
                amenities_json,
                "t",  # is_active
                "f",  # hourly_enabled
                created.isoformat(),
                created.isoformat(),
            ])
            prop_buf.write(prop_line + "\n")

            # Images (2-5 per property)
            num_images = random.randint(2, 5)
            for img_idx in range(num_images):
                img_id = gen_uuid()
                seed_val = img_seed_counter
                img_seed_counter += 1
                url = picsum_url(seed_val)
                is_primary = "t" if img_idx == 0 else "f"
                img_line = "\t".join([
                    img_id, pid, url, is_primary, str(img_idx),
                ])
                img_buf.write(img_line + "\n")

        prop_buf.seek(0)
        cur.copy_from(prop_buf, "properties", columns=[
            "id", "host_id", "title", "description", "city", "address",
            "latitude", "longitude", "price_per_night", "max_guests",
            "amenities", "is_active", "hourly_enabled", "created_at", "updated_at",
        ])

        img_buf.seek(0)
        cur.copy_from(img_buf, "property_images", columns=[
            "id", "property_id", "image_url", "is_primary", "sort_order",
        ])

        conn.commit()
        progress(end_i, args.properties, "Properties + images")

    print(f"  ✅ {args.properties:,} properties created with images")

    # ------------------------------------------------------------------
    # 5. Bookings
    # ------------------------------------------------------------------
    print(f"📅 Creating {args.bookings:,} bookings...")

    booking_ids = []
    completed_bookings = []  # (booking_id, property_id, guest_id) for reviews

    STATUSES = ["completed", "completed", "confirmed", "pending", "cancelled", "rejected"]
    # Weighted toward completed for more reviews

    BATCH = 10000
    num_batches = math.ceil(args.bookings / BATCH)

    for batch_idx in range(num_batches):
        start_i = batch_idx * BATCH
        end_i = min(start_i + BATCH, args.bookings)

        buf = io.StringIO()
        for i in range(start_i, end_i):
            bid = gen_uuid()
            pid = random.choice(property_ids)
            guest_id = random.choice(guest_ids)
            host_id = property_host_map[pid]
            price = property_price_map[pid]
            status = random.choice(STATUSES)

            # Generate check-in/check-out dates
            if status == "completed":
                check_in = random_date_between(NOW - timedelta(days=365), NOW - timedelta(days=10))
            elif status in ("confirmed", "pending"):
                check_in = random_date_between(NOW + timedelta(days=1), NOW + timedelta(days=180))
            else:
                check_in = random_date_between(NOW - timedelta(days=200), NOW + timedelta(days=60))

            nights = random.randint(1, 14)
            check_out = check_in + timedelta(days=nights)
            total_price = round(price * nights, 2)
            created = check_in - timedelta(days=random.randint(1, 30))

            booking_ids.append(bid)
            if status == "completed":
                completed_bookings.append((bid, pid, guest_id))

            line = "\t".join([
                bid, pid, guest_id, host_id,
                check_in.isoformat(), check_out.isoformat(),
                f"{total_price:.2f}",
                "nightly",  # booking_type
                "",  # hours (NULL)
                status,
                created.isoformat(),
                created.isoformat(),
            ])
            buf.write(line + "\n")

        buf.seek(0)
        cur.copy_from(buf, "bookings", columns=[
            "id", "property_id", "guest_id", "host_id",
            "check_in", "check_out", "total_price",
            "booking_type", "hours", "status",
            "created_at", "updated_at",
        ], null="")
        conn.commit()
        progress(end_i, args.bookings, "Bookings")

    print(f"  ✅ {args.bookings:,} bookings created ({len(completed_bookings):,} completed)")

    # ------------------------------------------------------------------
    # 6. Reviews (on completed bookings)
    # ------------------------------------------------------------------
    reviews_to_create = random.sample(
        completed_bookings,
        min(int(len(completed_bookings) * args.reviews_pct), len(completed_bookings)),
    )
    num_reviews = len(reviews_to_create)
    print(f"⭐ Creating {num_reviews:,} reviews...")

    BATCH = 10000
    num_batches = max(1, math.ceil(num_reviews / BATCH))

    for batch_idx in range(num_batches):
        start_i = batch_idx * BATCH
        end_i = min(start_i + BATCH, num_reviews)

        buf = io.StringIO()
        for i in range(start_i, end_i):
            bid, pid, guest_id = reviews_to_create[i]
            rid = gen_uuid()
            rating = round(random.uniform(2.0, 5.0), 1)
            comment = random.choice(REVIEW_COMMENTS)
            # Escape tabs/newlines in comment
            comment = comment.replace("\t", " ").replace("\n", " ")
            created = NOW - timedelta(days=random.randint(1, 300))

            line = "\t".join([
                rid, bid, pid, guest_id,
                f"{rating:.1f}",
                comment,
                created.isoformat(),
            ])
            buf.write(line + "\n")

        buf.seek(0)
        cur.copy_from(buf, "reviews", columns=[
            "id", "booking_id", "property_id", "reviewer_id",
            "rating", "comment", "created_at",
        ])
        conn.commit()
        progress(end_i, num_reviews, "Reviews")

    print(f"  ✅ {num_reviews:,} reviews created")

    # ------------------------------------------------------------------
    # 7. Conversations & Messages
    # ------------------------------------------------------------------
    num_convos = min(args.conversations, len(property_ids))
    msgs_per_convo = 3
    total_msgs = num_convos * msgs_per_convo
    print(f"💬 Creating {num_convos:,} conversations (~{total_msgs:,} messages)...")

    BATCH = 5000
    num_batches = max(1, math.ceil(num_convos / BATCH))

    for batch_idx in range(num_batches):
        start_i = batch_idx * BATCH
        end_i = min(start_i + BATCH, num_convos)

        conv_buf = io.StringIO()
        msg_buf = io.StringIO()

        for i in range(start_i, end_i):
            cid = gen_uuid()
            pid = property_ids[i % len(property_ids)]
            host_id = property_host_map[pid]
            guest_id = random.choice(guest_ids)
            created = random_date_between(NOW - timedelta(days=300), NOW - timedelta(days=1))

            conv_line = "\t".join([
                cid, pid, guest_id, host_id,
                created.isoformat(), created.isoformat(),
            ])
            conv_buf.write(conv_line + "\n")

            # Generate messages in the conversation
            msg_time = created
            for m in range(msgs_per_convo):
                mid = gen_uuid()
                sender = guest_id if m % 2 == 0 else host_id
                if m == 0:
                    content = random.choice([
                        "Hi, I'm interested in your property. Is it available for next month?",
                        "Hello! I have a question about the amenities listed.",
                        "Hey, love the photos! Can you tell me more about the neighborhood?",
                        "Hi there! What's the check-in process like?",
                        "Hello, is there parking available near the property?",
                    ])
                elif m % 2 == 1:
                    content = random.choice([
                        "Thank you for your interest! Yes, we have availability. When were you thinking?",
                        "Hi! Of course, what would you like to know?",
                        "Thanks! The neighborhood is very walkable with lots of restaurants nearby.",
                        "Hello! Check-in is self-service with a smart lock. I'll send the code the day before.",
                        "Yes, there's free street parking and a garage one block away.",
                    ])
                else:
                    content = random.choice([
                        "That sounds perfect, I'll go ahead and book!",
                        "Great, thank you for the quick response!",
                        "Awesome, looking forward to the stay!",
                        "Thanks for all the info, very helpful!",
                    ])

                content = content.replace("\t", " ").replace("\n", " ")
                msg_time = msg_time + timedelta(minutes=random.randint(5, 720))

                msg_line = "\t".join([
                    mid, cid, sender, content, "text",
                    "f",  # is_read
                    msg_time.isoformat(),
                ])
                msg_buf.write(msg_line + "\n")

        conv_buf.seek(0)
        cur.copy_from(conv_buf, "conversations", columns=[
            "id", "property_id", "guest_id", "host_id",
            "created_at", "updated_at",
        ])

        msg_buf.seek(0)
        cur.copy_from(msg_buf, "messages", columns=[
            "id", "conversation_id", "sender_id", "content",
            "message_type", "is_read", "created_at",
        ])

        conn.commit()
        progress(end_i, num_convos, "Conversations")

    print(f"  ✅ {num_convos:,} conversations with ~{total_msgs:,} messages")

    # ------------------------------------------------------------------
    # Done
    # ------------------------------------------------------------------
    cur.close()
    conn.close()

    elapsed = time.time() - t_start
    print()
    print("=" * 60)
    print(f"  ✅ Seeding complete in {elapsed:.1f}s")
    print("=" * 60)
    print()
    print("  📧 Admin login:  admin@staynest.com / TestPass123!")
    print("  📧 Host logins:  host1@staynest.com ... host500@staynest.com / TestPass123!")
    print("  📧 Guest logins: guest1@staynest.com ... guest5000@staynest.com / TestPass123!")
    print()
    print("  Quick test:")
    print("    curl http://localhost:8000/api/v1/properties?limit=10")
    print()


if __name__ == "__main__":
    main()
