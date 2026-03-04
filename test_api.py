import os
import sys

# 1. Parse .env and set env vars BEFORE importing app
with open('/opt/timetracker/.env', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            k, v = line.split('=', 1)
            # Remove possible quotes
            v = v.strip("'").strip('"')
            os.environ[k] = v

sys.path.append("/opt/timetracker")
from app import app, get_db_connection
import uuid
import json

client = app.test_client()

# 2. Register test user
unique_id = str(uuid.uuid4())[:8]
username = f"testadmin_{unique_id}"
email = f"{username}@example.com"

print(f"[*] Registering user {username}...")
r1 = client.post("/register", json={
    "username": username,
    "email": email,
    "password": "password123",
    "full_name": "Test Admin"
})
print("Register response:", r1.status_code, r1.get_data(as_text=True))

# 3. Promote to Admin
print("[*] Promoting to admin...")
conn = get_db_connection()
cur = conn.cursor()
cur.execute("UPDATE users SET role = 'admin' WHERE username = %s", (username,))
conn.commit()
cur.close()
conn.close()

# 4. Login
print("[*] Logging in...")
r2 = client.post("/login", json={
    "username": username,
    "password": "password123"
})
print("Login response:", r2.status_code, r2.get_data(as_text=True))

# 5. Test Reporting API without dates
print("\n[*] Testing /api/reports/summary (No dates provided)")
r3 = client.get("/api/reports/summary")
print("Status:", r3.status_code)
if r3.status_code == 200:
    data = r3.get_json()
    print("Keys in response:", list(data.keys()))
    print("Date Range parsed:", data.get('date_range'))
    print(f"Projects count: {len(data.get('projects', []))}")
    print(f"Users count: {len(data.get('users', []))}")
else:
    print("Error:", r3.get_data(as_text=True))

# 6. Test with dates
print("\n[*] Testing /api/reports/summary (With dates provided)")
r4 = client.get("/api/reports/summary?start_date=2024-01-01&end_date=2024-12-31")
print("Status:", r4.status_code)
if r4.status_code == 200:
    data = r4.get_json()
    print("Date Range parsed:", data.get('date_range'))
else:
    print("Error:", r4.get_data(as_text=True))

# 7. Test with normal user to ensure 403
print("\n[*] Testing with normal user...")
normal_user = f"testuser_{unique_id}"
client.post("/register", json={
    "username": normal_user,
    "email": f"{normal_user}@example.com",
    "password": "password123",
    "full_name": "Test User"
})
# Important: logging in sets the session for the test_client
client.post("/login", json={
    "username": normal_user,
    "password": "password123"
})
r5 = client.get("/api/reports/summary")
print("Normal User Status:", r5.status_code)

print("\n[*] Tests complete.")
