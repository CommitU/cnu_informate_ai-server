import os, pymysql
from dotenv import load_dotenv
load_dotenv()
def get_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST","127.0.0.1"),
        port=int(os.getenv("DB_PORT","3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )

def upsert_notice(cur, source_id, url, title, content, posted_at, hash_):
    sql = """
      INSERT INTO notice (source_id,url,title,content,posted_at,hash)
      VALUES (%s,%s,%s,%s,%s,%s)
      ON DUPLICATE KEY UPDATE
        title=VALUES(title), content=VALUES(content), posted_at=VALUES(posted_at)
    """
    cur.execute(sql, (source_id, url, title, content, posted_at, hash_))
    cur.execute("SELECT id FROM notice WHERE url=%s", (url,))
    return cur.fetchone()["id"]

def insert_notice_category(cur, notice_id, category_id, conf, model_ver):
    sql = """
      INSERT INTO notice_category (notice_id,category_id,confidence,model_version)
      VALUES (%s,%s,%s,%s)
      ON DUPLICATE KEY UPDATE confidence=VALUES(confidence), model_version=VALUES(model_version)
    """
    cur.execute(sql, (notice_id, category_id, conf, model_ver))