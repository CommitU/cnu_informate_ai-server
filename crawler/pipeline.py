# pipeline.py
import time
import random
import hashlib
from typing import Optional, Dict, Iterable, Tuple, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from db import get_conn, upsert_notice, insert_notice_category
from classifier_stub import classify

# ---------------------------------------------------------
# 소스 정의
#  - type: "board" | "recruit"
#  - board: code, menu_dvs_cd 필요
#  - recruit: menu_dvs_cd 필요
#  - source_id는 DB seed와 일치해야 함
# ---------------------------------------------------------
SOURCES: List[Dict] = [
    # _prog/_board/
    {"source_id": 1, "name": "메인-0704",   "type": "board",   "code": "sub07_0704", "menu_dvs_cd": "0704"},
    {"source_id": 2, "name": "메인-0709",   "type": "board",   "code": "sub07_0709", "menu_dvs_cd": "0709"},
    {"source_id": 3, "name": "메인-0705",   "type": "board",   "code": "sub07_0705", "menu_dvs_cd": "0705"},
    {"source_id": 4, "name": "메인-070808", "type": "board",   "code": "sub07_070808", "menu_dvs_cd": "070808"},
    # _prog/recruit/
    {"source_id": 5, "name": "리크루트-07080401", "type": "recruit", "menu_dvs_cd": "07080401"},
]

# ---------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (CNU-InfoMate/0.2; +https://plus.cnu.ac.kr)"
}
RETRY_STATUS = {500, 502, 503, 504}

def delay():
    time.sleep(random.uniform(0.8, 1.8))

def req_get(url: str, params: Optional[Dict] = None, timeout: int = 15, max_retry: int = 2) -> Optional[requests.Response]:
    """5xx/일부 네트워크 에러 재시도"""
    for attempt in range(max_retry + 1):
        try:
            res = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=timeout)
            if res.status_code in RETRY_STATUS and attempt < max_retry:
                delay()
                continue
            res.raise_for_status()
            res.encoding = 'utf-8'
            return res
        except Exception as e:
            if attempt >= max_retry:
                print(f"[ERR] GET fail url={url} params={params} err={e}")
                return None
            delay()
    return None

def make_hash(title: str, content: Optional[str]) -> str:
    h = hashlib.sha256()
    h.update((title + "|" + (content or "")).encode("utf-8"))
    return h.hexdigest()

# ---------------------------------------------------------
# 어댑터: _prog/_board
# ---------------------------------------------------------
class BoardAdapter:
    BASE = "https://plus.cnu.ac.kr/_prog/_board/"

    @staticmethod
    def fetch_page(code: str, menu_dvs_cd: str, page: int) -> Optional[str]:
        params = {
            "code": code,
            "site_dvs_cd": "kr",
            "menu_dvs_cd": menu_dvs_cd,
            "skey": "",
            "sval": "",
            "site_dvs": "",
            "ntt_tag": "",
            "GotoPage": page,
        }
        res = req_get(BoardAdapter.BASE, params=params)
        return res.text if res else None

    @staticmethod
    def parse_list(html: str) -> Iterable[Tuple[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.select("td.title a"):
            href = a.get("href")
            if not href:
                continue
            title = a.get_text(strip=True)
            url = urljoin(BoardAdapter.BASE, href)
            yield title, url

    @staticmethod
    def fetch_detail(url: str) -> Tuple[str, Optional[str]]:
        res = req_get(url)
        if not res:
            return "", None
        soup = BeautifulSoup(res.text, "html.parser")
        # 본문
        detail_div = soup.find("div", class_="board_viewDetail")
        content = detail_div.get_text(" ", strip=True) if detail_div else ""
        # 게시일(YYYY-MM-DD) 추출 시도
        date_text = None
        info = soup.select_one(".board_view .top_info, .view_info, .board_view .viewtop, .board_view .info")
        if info:
            import re
            m = re.search(r"\d{4}-\d{2}-\d{2}", info.get_text(" ", strip=True))
            if m:
                date_text = m.group(0)
        return content, date_text

# ---------------------------------------------------------
# 어댑터: _prog/recruit
# ---------------------------------------------------------
class RecruitAdapter:
    BASE = "https://plus.cnu.ac.kr/_prog/recruit/"

    @staticmethod
    def fetch_page(menu_dvs_cd: str, page: int) -> Optional[str]:
        params = {
            "menu_dvs_cd": menu_dvs_cd,
            "site_dvs_cd": "kr",
            "GotoPage": page,
        }
        res = req_get(RecruitAdapter.BASE, params=params)
        return res.text if res else None

    @staticmethod
    def parse_list(html: str) -> Iterable[Tuple[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        # 다양한 마크업에 대응
        for a in soup.select("td.title a, .title a, .subject a"):
            href = a.get("href")
            if not href:
                continue
            title = a.get_text(strip=True)
            url = urljoin(RecruitAdapter.BASE, href)
            yield title, url

    @staticmethod
    def fetch_detail(url: str) -> Tuple[str, Optional[str]]:
        res = req_get(url)
        if not res:
            return "", None
        soup = BeautifulSoup(res.text, "html.parser")
        content_area = soup.select_one(".board_viewDetail, .view_con, .content, .bbs_view")
        content = content_area.get_text(" ", strip=True) if content_area else ""
        # 게시일(YYYY-MM-DD) 추출 시도
        date_text = None
        info = soup.select_one(".board_view .top_info, .bbs_view .info, .view_info, .meta")
        if info:
            import re
            m = re.search(r"\d{4}-\d{2}-\d{2}", info.get_text(" ", strip=True))
            if m:
                date_text = m.group(0)
        return content, date_text

# ---------------------------------------------------------
# 파이프라인
# ---------------------------------------------------------
def run(pages: int = 2):
    with get_conn() as conn:
        with conn.cursor() as cur:
            for src in SOURCES:
                sid = src["source_id"]
                sname = src["name"]
                stype = src["type"]
                print(f"\n[START] source={sid}:{sname} pages={pages}")

                for page in range(1, pages + 1):
                    delay()
                    if stype == "board":
                        html = BoardAdapter.fetch_page(src["code"], src["menu_dvs_cd"], page)
                    else:
                        html = RecruitAdapter.fetch_page(src["menu_dvs_cd"], page)

                    if not html:
                        print(f"[SKIP] source={sid} page={page} fetch failed")
                        continue

                    count_on_page = 0
                    parser = BoardAdapter.parse_list if stype == "board" else RecruitAdapter.parse_list
                    fetcher = BoardAdapter.fetch_detail if stype == "board" else RecruitAdapter.fetch_detail

                    for title, url in parser(html):
                        delay()
                        content, posted_at = fetcher(url)
                        if content == "" and posted_at is None:
                            print(f"[SKIP] detail fetch failed {url}")
                            continue

                        nid = upsert_notice(
                            cur,
                            sid,
                            url,
                            title,
                            content,
                            posted_at,
                            make_hash(title, content),
                        )

                        cat_id, conf, ver = classify(title, content)
                        insert_notice_category(cur, nid, cat_id, conf, ver)

                        count_on_page += 1
                        print(f"[OK] src={sid} p={page} notice={nid} {title[:40]}...")

                    print(f"[PAGE DONE] source={sid} page={page} items={count_on_page}")

                print(f"[DONE] source={sid}:{sname}")

if __name__ == "__main__":
    run(pages=2)