import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional, Dict, List, Tuple

BASE = "https://plus.cnu.ac.kr/_prog/_board/"
PARAMS = {
    "code": "sub07_0702",
    "site_dvs_cd": "kr",
    "menu_dvs_cd": "0702",
    "skey": "",
    "sval": "",
    "site_dvs": "",
    "ntt_tag": "",
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (CNU-InfoMate/0.1; +https://plus.cnu.ac.kr)"
}

def delay() -> None:
    """요청 간 랜덤 지연(차단 방지)"""
    time.sleep(random.uniform(1.0, 2.5))

# ---------------------------
# 재시도 유틸
# ---------------------------
RETRY_STATUS = {500, 502, 503, 504}  # 서버측 문제만 재시도

def request_with_retry(
    url: str,
    params: Optional[Dict] = None,
    timeout: int = 20,
    max_retries: int = 3,
    backoff_factor: float = 1.6,
    headers: Optional[Dict] = None,
) -> Optional[requests.Response]:
    """
    requests.get에 재시도(지수 백오프 + 지터)를 적용.
    - 재시도 대상: 타임아웃/연결오류/5xx
    - 4xx는 재시도하지 않음
    실패 시 None 반환
    """
    headers = headers or DEFAULT_HEADERS
    attempt = 0
    while attempt <= max_retries:
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code in RETRY_STATUS:
                # 5xx는 재시도
                raise requests.HTTPError("retryable", response=resp)
            return resp
        except (requests.ConnectTimeout, requests.ReadTimeout):
            pass  # 타임아웃 → 재시도
        except (requests.ConnectionError, requests.ChunkedEncodingError, requests.HTTPError) as e:
            # 4xx면 즉시 포기
            if isinstance(e, requests.HTTPError) and getattr(e, "response", None) is not None:
                if 400 <= e.response.status_code < 500:
                    print("[SKIP 4xx] {} -> {}".format(url, e.response.status_code))
                    return None
        except Exception as e:
            print("[ERROR] {} -> {}: {}".format(url, type(e).__name__, e))
            return None

        if attempt == max_retries:
            print("[GIVEUP] {} after {} retries".format(url, max_retries))
            return None

        sleep_s = (backoff_factor ** attempt) + random.uniform(0, 0.3)
        print("[RETRY {}/{}] waiting {:.2f}s for {}".format(attempt + 1, max_retries, sleep_s, url))
        time.sleep(sleep_s)
        attempt += 1

    return None

# ---------------------------
# 목록/상세 크롤러
# ---------------------------
def fetch_page(page: int) -> Optional[str]:
    """목록 페이지 HTML 반환(재시도 적용)"""
    delay()
    p = dict(PARAMS)
    p["GotoPage"] = page
    resp = request_with_retry(BASE, params=p, timeout=20, max_retries=3)
    if not resp:
        return None
    resp.encoding = "utf-8"
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        print("[HTTP {}] list page {} -> skip".format(resp.status_code, page))
        return None
    return resp.text

def parse_list(html: str) -> List[Tuple[str, str]]:
    """목록 HTML에서 (제목, 상세링크) 추출"""
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.select("td.title a")
    pairs: List[Tuple[str, str]] = []
    for a in anchors:
        href = a.get("href")
        if not href:
            continue
        pairs.append((a.get_text(strip=True), urljoin(BASE, href)))
    return pairs

def fetch_detail(url: str) -> Tuple[str, Optional[str]]:
    """
    상세 페이지에서 (본문, 게시일) 추출 (재시도 적용)
    게시일 파싱이 불안정하면 None 반환
    """
    delay()
    resp = request_with_retry(url, timeout=20, max_retries=3)
    if not resp:
        return "", None
    resp.encoding = "utf-8"
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        print("[HTTP {}] detail -> skip {}".format(resp.status_code, url))
        return "", None

    soup = BeautifulSoup(resp.text, "html.parser")
    detail = soup.select_one("div.board_viewDetail")
    content = detail.get_text(" ", strip=True) if detail else ""
    posted_at = None  # TODO: 필요 시 상단 info 영역에서 파싱
    return content, posted_at