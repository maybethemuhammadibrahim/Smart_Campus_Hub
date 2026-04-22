from werkzeug.security import generate_password_hash
from db_connector import execute_query

h = generate_password_hash("1234")
execute_query("UPDATE users SET password = %s", (h,), fetch=False)
print("All users now have password: 1234")
rows = execute_query("SELECT username, role FROM users")
for r in rows:
    print(f"  {r['username']:15s} | {r['role']}")
