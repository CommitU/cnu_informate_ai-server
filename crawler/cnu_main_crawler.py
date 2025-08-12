import time
import random
from typing import Optional, Dict, List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 새 파이프라인의 어댑터를 재사용 (동일 디렉터리에 pipeline의 어댑터가 있다고 가정)
# 만약 모듈 경로가 다르면 적절히 변경해줘.
from pipeline import BoardAdapter  # type: ignore

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (CNU-InfoMate/0.2; +https://plus.cnu.ac.kr)"
}

def delay() -> None:
    time.sleep(random.uniform(0.8, 1.8))

# 기본 파라미터(레거시): 메인 게시판 하나를 가정.
BASE = "https://plus.cnu.ac.kr/_prog/_board/"
DEFAULT_CODE = "sub07_0702"
DEFAULT_MENU = "0702"

def fetch_page(page: int, code: str = DEFAULT_CODE, menu_dvs_cd: str = DEFAULT_MENU) -> Optional[str]:
    """레거시 함수 시그니처 유지. 내부는 BoardAdapter 호출."""
    delay()
    return BoardAdapter.fetch_page(code, menu_dvs_cd, page)

def parse_list(html: str) -> List[Tuple[str, str]]:
    """(제목, 상세링크) 리스트"""
    pairs: List[Tuple[str, str]] = []
    for title, url in BoardAdapter.parse_list(html):
        pairs.append((title, url))
    return pairs

def fetch_detail(url: str) -> Tuple[str, Optional[str]]:
    """
    (본문, 게시일 YYYY-MM-DD|None)
    """
    delay()
    content, posted_at = BoardAdapter.fetch_detail(url)
    return content, posted_at