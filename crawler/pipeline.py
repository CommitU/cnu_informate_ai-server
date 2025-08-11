import hashlib
from db import get_conn, upsert_notice, insert_notice_category
from cnu_main_crawler import fetch_page, parse_list, fetch_detail
from classifier_stub import classify

SOURCE_ID_MAIN = 1  # source 시드의 PK

def make_hash(title, content):
    h = hashlib.sha256(); h.update((title + "|" + (content or "")).encode("utf-8"))
    return h.hexdigest()

# pipeline.py (변경된 부분만 예시)

def run(pages=2):
    with get_conn() as conn:
        with conn.cursor() as cur:
            for page in range(1, pages+1):
                html = fetch_page(page)
                if not html:
                    print(f"[SKIP] page {page} fetch failed")
                    continue

                for title, url in parse_list(html):
                    content, posted_at = fetch_detail(url)
                    if content == "" and posted_at is None:
                        print(f"[SKIP] detail fetch failed {url}")
                        continue

                    nid = upsert_notice(cur, SOURCE_ID_MAIN, url, title, content, posted_at, make_hash(title, content))
                    cat_id, conf, ver = classify(title, content)
                    insert_notice_category(cur, nid, cat_id, conf, ver)
                    print(f"[OK] notice={nid} {title[:40]}...")

if __name__ == "__main__":
    run(pages=2)