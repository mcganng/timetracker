import requests
import psycopg2
import uuid

unique_id = str(uuid.uuid4())[:8]
username = f"testadmin_{unique_id}"
email = f"{username}@example.com"

print(f"[*] Registering user {username}...")
r1 = requests.post("http://localhost:5000/register", json={
    "username": username,
    "email": email,
    "password": "password123",
    "full_name": "Test Admin"
})
print("Register response:", r1.status_code, r1.text)

print("[*] Promoting to admin...")
import sys
sys.path.append("/opt/timetracker")
from app import get_db_connection

conn = get_db_connection()
cur = conn.cursor()
cur.execute("UPDATE users SET role = 'admin' WHERE username = %s", (username,))
conn.commit()
cur.close()
conn.close()

print("[*] Logging in...")
session = requests.Session()
r2 = session.post("http://localhost:5000/login", json={
    "username": username,
    "password": "password123"
})

print("\n[*] Testing /admin/reports (UI Generation)")
r3 = session.get("http://localhost:5000/admin/reports")
print("Status:", r3.status_code)
if r3.status_code == 200:
    content = r3.text
    print("Found 'System Reports' heading:", "<h2><i class=\"bi bi-graph-up\"></i> System Reports</h2>" in content)
    print("Found 'Report Filters' section:", "Report Filters" in content)
    print("Found Javascript fetch function:", "async function fetchReportData()" in content)
else:
    print("Error:", r3.text[:200])

print("\n[*] Tests complete.")
