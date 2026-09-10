import sqlite3
conn = sqlite3.connect('corp_mail_outreach.db')
rows = conn.execute('SELECT * FROM send_log ORDER BY rowid DESC LIMIT 20').fetchall()
for r in rows:
    print(r)
