from database import get_connection
conn = get_connection()
try:
    conn.execute("ALTER TABLE journal_entries ADD COLUMN entity TEXT DEFAULT ''")
    conn.commit()
    print("Column 'entity' added to journal_entries")
except Exception as e:
    print("Already exists or error:", e)
conn.close()
