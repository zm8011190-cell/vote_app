import os
import sqlite3
import models

print('db_path=', models.DB_PATH)
print('exists=', os.path.exists(models.DB_PATH))
conn = sqlite3.connect(models.DB_PATH)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='addphoto'")
print('addphoto_exists=', cur.fetchone() is not None)
cur.execute('PRAGMA table_info(addphoto)')
print('columns=', cur.fetchall())
conn.close()
