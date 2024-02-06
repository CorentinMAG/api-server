from .. import db
from psycopg import sql

def flush():
    conn = db.get_db()
    cur = conn.cursor()

    # disable foreign key checks temporarily
    cur.execute("SET session_replication_role = replica")

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cur.fetchall()
    for table in tables:
        cur.execute(sql.SQL("TRUNCATE TABLE {} CASCADE").format(sql.Identifier(table[0])))
    conn.commit()

    # re-enable foreign key checks
    cur.execute("SET session_replication_role = DEFAULT")
    cur.close()