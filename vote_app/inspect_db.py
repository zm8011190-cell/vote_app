import os
import sqlite3

files = [r'C:\Users\zm801\OneDrive\Desktop\project\vote_app\users.db', r'C:\Users\zm801\OneDrive\Desktop\project\users.db']

for f in files:
    print('FILE', f, 'exists=', os.path.exists(f))
    if os.path.exists(f):
        conn = sqlite3.connect(f)
        cur = conn.cursor()
        cur.execute("select name from sqlite_master where type='table'")
        print('tables=', cur.fetchall())
        for table in ['questions', 'users']:
            try:
                cur.execute('select count(*) from ' + table)
                print(table, 'count=', cur.fetchone()[0])
            except Exception as e:
                print(table, 'err=', e)
        conn.close()
