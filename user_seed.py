import sqlite3
import bcrypt

conn = sqlite3.connect('tracker.db')
c = conn.cursor()

username = 'user1'
email = 'user1@email.com'
password = 'user123'
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

try:
    c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, hashed))
    conn.commit()
    print("User added successfully!")
except sqlite3.IntegrityError:
    print("User already exists.")
conn.close()
