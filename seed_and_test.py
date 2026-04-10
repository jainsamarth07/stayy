"""
StayNest — Database Setup & End-to-End API Smoke Test
=====================================================
Run this AFTER your backend (uvicorn) and database (postgres) are running.

Usage:
  python seed_and_test.py              # default: http://localhost:8000
  python seed_and_test.py http://localhost:8000   # custom base URL

What it does:
  1. Registers a regular USER, a HOST, and manually promotes an ADMIN
  2. Tests auth flows (login, token refresh, profile)
  3. Host creates a property listing
  4. Guest searches & views properties
  5. Guest books a property
  6. Host confirms the booking
  7. Guest writes a review after checkout
  8. Admin dashboard & user management
  9. Messaging between guest and host
  10. Membership purchase for the host
"""

import sys
import json
import uuid
import httpx
from datetime import datetime, timedelta

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
API = f"{BASE}/api/v1"

# Pretty print helper
def pp(label: str, resp: httpx.Response) -> dict | list | str:
    status = resp.status_code
    try:
        data = resp.json()
    except Exception:
        data = resp.text
    icon = "✅" if 200 <= status < 400 else "❌"
    print(f"\n{icon} [{status}] {label}")
    if isinstance(data, dict):
        print(json.dumps(data, indent=2, default=str)[:800])
    else:
        print(str(data)[:400])
    return data


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main():
    client = httpx.Client(base_url=API, timeout=30)

    print("=" * 60)
    print("  StayNest — Full End-to-End Smoke Test")
    print("=" * 60)

    # ------------------------------------------------------------------
    # STEP 0 — Health check
    # ------------------------------------------------------------------
    print("\n--- Step 0: Health Check ---")
    r = client.get(f"{BASE}/health")
    pp("Health Check", r)
    if r.status_code != 200:
        print("⚠️  Backend not reachable. Make sure it's running!")
        sys.exit(1)

    # ------------------------------------------------------------------
    # STEP 1 — Register users
    # ------------------------------------------------------------------
    ts = datetime.now().strftime("%H%M%S")  # unique suffix

    guest_email = f"guest_{ts}@example.com"
    host_email = f"host_{ts}@example.com"
    admin_email = f"admin_{ts}@example.com"
    password = "SecurePass123!"

    print("\n--- Step 1: Register Users ---")

    # 1a — Guest (role=user)
    r = client.post("/auth/register", json={
        "email": guest_email,
        "password": password,
        "full_name": "Alice Guest",
        "role": "user"
    })
    guest_data = pp("Register Guest", r)
    guest_id = guest_data.get("id") if isinstance(guest_data, dict) else None

    # 1b — Host (role=host)
    r = client.post("/auth/register", json={
        "email": host_email,
        "password": password,
        "full_name": "Bob Host",
        "role": "host"
    })
    host_data = pp("Register Host", r)
    host_id = host_data.get("id") if isinstance(host_data, dict) else None

    # 1c — Admin: register as user first, then we'll promote via SQL later
    r = client.post("/auth/register", json={
        "email": admin_email,
        "password": password,
        "full_name": "Charlie Admin",
        "role": "user"
    })
    admin_data = pp("Register Admin (as user first)", r)
    admin_id = admin_data.get("id") if isinstance(admin_data, dict) else None

    # ------------------------------------------------------------------
    # STEP 2 — Login all three users
    # ------------------------------------------------------------------
    print("\n--- Step 2: Login Users ---")

    r = client.post("/auth/login", json={"email": guest_email, "password": password})
    guest_tokens = pp("Login Guest", r)
    guest_access = guest_tokens.get("access_token", "") if isinstance(guest_tokens, dict) else ""

    r = client.post("/auth/login", json={"email": host_email, "password": password})
    host_tokens = pp("Login Host", r)
    host_access = host_tokens.get("access_token", "") if isinstance(host_tokens, dict) else ""

    r = client.post("/auth/login", json={"email": admin_email, "password": password})
    admin_tokens = pp("Login Admin (still user role)", r)
    admin_access = admin_tokens.get("access_token", "") if isinstance(admin_tokens, dict) else ""

    # ------------------------------------------------------------------
    # STEP 2b — Token refresh test
    # ------------------------------------------------------------------
    print("\n--- Step 2b: Token Refresh ---")
    if isinstance(guest_tokens, dict) and guest_tokens.get("refresh_token"):
        r = client.post("/auth/refresh", json={"refresh_token": guest_tokens["refresh_token"]})
        refreshed = pp("Refresh Guest Token", r)
        if isinstance(refreshed, dict) and refreshed.get("access_token"):
            guest_access = refreshed["access_token"]

    # ------------------------------------------------------------------
    # STEP 2c — Get profile
    # ------------------------------------------------------------------
    print("\n--- Step 2c: Get Profile ---")
    r = client.get("/auth/me", headers=auth_header(guest_access))
    pp("Guest Profile", r)

    r = client.get("/auth/me", headers=auth_header(host_access))
    pp("Host Profile", r)

    # ------------------------------------------------------------------
    # STEP 3 — HOST creates a property
    # ------------------------------------------------------------------
    print("\n--- Step 3: Host Creates Property ---")
    r = client.post("/properties", headers=auth_header(host_access), json={
        "title": "Cozy Downtown Apartment",
        "description": "Beautiful 2-bedroom apartment in the heart of downtown with great views.",
        "city": "New York",
        "address": "123 Main Street, Apt 4B, New York, NY 10001",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "price_per_night": 150.00,
        "max_guests": 4,
        "amenities": ["wifi", "kitchen", "air_conditioning", "washer"]
    })
    property_data = pp("Create Property", r)
    property_id = property_data.get("id") if isinstance(property_data, dict) else None

    # Create a second property
    r = client.post("/properties", headers=auth_header(host_access), json={
        "title": "Beach House Paradise",
        "description": "Stunning beachfront house with panoramic ocean views and private pool.",
        "city": "Miami",
        "address": "456 Ocean Drive, Miami Beach, FL 33139",
        "latitude": 25.7617,
        "longitude": -80.1918,
        "price_per_night": 300.00,
        "max_guests": 8,
        "amenities": ["wifi", "pool", "beach_access", "parking", "air_conditioning"]
    })
    property2_data = pp("Create Second Property", r)

    # ------------------------------------------------------------------
    # STEP 4 — GUEST browses properties
    # ------------------------------------------------------------------
    print("\n--- Step 4: Browse Properties ---")

    r = client.get("/properties")
    pp("List All Properties", r)

    r = client.get("/properties", params={"city": "New York"})
    pp("Search Properties in New York", r)

    if property_id:
        r = client.get(f"/properties/{property_id}")
        pp(f"Get Property Detail ({property_id[:8]}...)", r)

    # ------------------------------------------------------------------
    # STEP 5 — GUEST books a property
    # ------------------------------------------------------------------
    print("\n--- Step 5: Guest Books Property ---")
    check_in = (datetime.now() + timedelta(days=7)).isoformat()
    check_out = (datetime.now() + timedelta(days=10)).isoformat()

    if property_id:
        r = client.post("/bookings", headers=auth_header(guest_access), json={
            "property_id": property_id,
            "check_in": check_in,
            "check_out": check_out,
            "booking_type": "nightly"
        })
        booking_data = pp("Create Booking (3 nights)", r)
        booking_id = booking_data.get("id") if isinstance(booking_data, dict) else None
    else:
        booking_id = None
        print("⚠️  Skipping booking — no property_id.")

    # ------------------------------------------------------------------
    # STEP 5b — List bookings
    # ------------------------------------------------------------------
    print("\n--- Step 5b: List Bookings ---")
    r = client.get("/bookings", headers=auth_header(guest_access))
    pp("Guest's Bookings", r)

    r = client.get("/bookings", headers=auth_header(host_access))
    pp("Host's Bookings", r)

    # ------------------------------------------------------------------
    # STEP 6 — HOST confirms booking
    # ------------------------------------------------------------------
    print("\n--- Step 6: Host Confirms Booking ---")
    if booking_id:
        r = client.put(f"/bookings/{booking_id}/status",
                         headers=auth_header(host_access),
                         json={"status": "confirmed"})
        pp("Confirm Booking", r)
    else:
        print("⚠️  Skipping — no booking_id.")

    # ------------------------------------------------------------------
    # STEP 7 — Guest writes a review (after marking completed)
    # ------------------------------------------------------------------
    print("\n--- Step 7: Review Flow ---")
    if booking_id:
        # Complete the booking first
        r = client.put(f"/bookings/{booking_id}/status",
                         headers=auth_header(host_access),
                         json={"status": "completed"})
        pp("Complete Booking", r)

        # Guest writes a review
        r = client.post("/reviews", headers=auth_header(guest_access), json={
            "booking_id": booking_id,
            "rating": 5,
            "comment": "Amazing apartment! The views were incredible and Bob was a great host."
        })
        pp("Submit Review", r)

        # List reviews for the property
        if property_id:
            r = client.get(f"/reviews/property/{property_id}")
            pp("Property Reviews", r)
    else:
        print("⚠️  Skipping reviews — no booking.")

    # ------------------------------------------------------------------
    # STEP 8 — Messaging between guest and host
    # ------------------------------------------------------------------
    print("\n--- Step 8: Messaging ---")
    if property_id and guest_id and host_id:
        # Guest starts a conversation about the property
        r = client.post("/conversations", headers=auth_header(guest_access), json={
            "property_id": property_id,
            "message": "Hi Bob! I loved the apartment. Are there any restaurants nearby?"
        })
        conv_data = pp("Guest Starts Conversation", r)
        conv_id = conv_data.get("id") if isinstance(conv_data, dict) else None

        # Host replies in the same conversation
        if conv_id:
            r = client.post(f"/conversations/{conv_id}/messages", headers=auth_header(host_access), json={
                "content": "Thanks Alice! Yes, there are great restaurants within walking distance."
            })
            pp("Host Replies", r)

        # Guest views conversations
        r = client.get("/conversations", headers=auth_header(guest_access))
        pp("Guest's Conversations", r)
    else:
        print("⚠️  Skipping messaging — missing user/property IDs.")

    # ------------------------------------------------------------------
    # STEP 9 — Membership for host
    # ------------------------------------------------------------------
    print("\n--- Step 9: Host Membership ---")
    r = client.post("/memberships/subscribe", headers=auth_header(host_access), json={
        "plan_type": "premium",
        "payment_token": "tok_test_seed"
    })
    pp("Host Subscribes to Premium", r)

    r = client.get("/memberships/current", headers=auth_header(host_access))
    pp("Host's Membership", r)

    # ------------------------------------------------------------------
    # STEP 10 — Admin operations
    #   NOTE: The admin user must be promoted in the DB first!
    #   See instructions printed below.
    # ------------------------------------------------------------------
    print("\n--- Step 10: Admin Operations ---")
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  To test admin endpoints, promote the admin user in the DB: ║
║                                                              ║
║  Using psql (Docker):                                        ║
║    docker exec -it <db_container> psql -U staynest staynest  ║
║                                                              ║
║  Or if Postgres is local:                                    ║
║    psql -U staynest -d staynest                              ║
║                                                              ║
║  Then run:                                                   ║
║    UPDATE users SET role = 'admin'                           ║
║    WHERE email = '{admin_email}';                            ║
║                                                              ║
║  Then re-login below to get admin-role JWT.                  ║
╚══════════════════════════════════════════════════════════════╝
""")

    # Try admin endpoints with current token (will fail if not promoted)
    r = client.get("/admin/dashboard", headers=auth_header(admin_access))
    result = pp("Admin Dashboard (may fail if not promoted yet)", r)

    if r.status_code == 403:
        print("\n⏳ Attempting to re-login admin after potential DB promotion...")
        r = client.post("/auth/login", json={"email": admin_email, "password": password})
        admin_tokens2 = pp("Re-login Admin", r)
        if isinstance(admin_tokens2, dict) and admin_tokens2.get("access_token"):
            admin_access2 = admin_tokens2["access_token"]

            r = client.get("/admin/dashboard", headers=auth_header(admin_access2))
            pp("Admin Dashboard (after promotion)", r)

            r = client.get("/admin/users", headers=auth_header(admin_access2))
            pp("Admin — List Users", r)

            r = client.get("/admin/properties", headers=auth_header(admin_access2))
            pp("Admin — List Properties", r)

            r = client.get("/admin/memberships", headers=auth_header(admin_access2))
            pp("Admin — List Memberships", r)

            # Toggle a user's status
            if guest_id:
                r = client.put(f"/admin/users/{guest_id}/status",
                               headers=auth_header(admin_access2))
                pp("Admin — Toggle Guest Active Status", r)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)
    print(f"""
  Guest email : {guest_email}
  Host email  : {host_email}
  Admin email : {admin_email}
  Password    : {password}
  Property ID : {property_id or 'N/A'}
  Booking ID  : {booking_id or 'N/A'}

  Frontend    : http://localhost:3000
  Swagger UI  : {BASE}/docs
  ReDoc       : {BASE}/redoc
""")


if __name__ == "__main__":
    main()
