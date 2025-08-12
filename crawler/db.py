import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        charset="utf8mb4",
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor,
    )
    # 연결 유지를 위해 즉시 ping (이미 끊겨있을 경우 재연결)
    try:
        conn.ping(reconnect=True)
    except Exception:
        pass
    return conn


def upsert_notice(cur, source_id, url, title, content, posted_at, hash_):
    """
    - url 또는 hash 중 하나 이상에 UNIQUE 제약이 있어야 함.
    - LAST_INSERT_ID(id) 패턴으로 항상 cursor.lastrowid 통해 id를 회수 가능.
    """
    sql = """
      INSERT INTO notice (source_id, url, title, content, posted_at, hash)
      VALUES (%s, %s, %s, %s, %s, %s)
      ON DUPLICATE KEY UPDATE
        id = LAST_INSERT_ID(id),
        title = VALUES(title),
        content = VALUES(content),
        posted_at = VALUES(posted_at),
        hash = VALUES(hash)
    """
    cur.execute(sql, (source_id, url, title, content, posted_at, hash_))
    # cursor.lastrowid가 insert이든 update든 id를 돌려줌
    return cur.lastrowid


def insert_notice_category(cur, notice_id, category_id, conf, model_ver):
    """
    - 대표 카테고리 1개 가정: notice_category.notice_id UNIQUE
      (여러 개 저장하려면 UNIQUE(notice_id, category_id)로 바꾸고 SQL도 약간 수정)
    """
    sql = """
      INSERT INTO notice_category (notice_id, category_id, confidence, model_version)
      VALUES (%s, %s, %s, %s)
      ON DUPLICATE KEY UPDATE
        category_id = VALUES(category_id),
        confidence = VALUES(confidence),
        model_version = VALUES(model_version)
    """
    cur.execute(sql, (notice_id, category_id, conf, model_ver))