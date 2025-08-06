import csv
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict


class CnuMainCrawling:
    def __init__(self, code, pages, fields=None, category=None):
        self.base_url = "https://plus.cnu.ac.kr/_prog/_board/"
        self.params = {
            "code": code,
            "site_dvs_cd": "kr",
            "menu_dvs_cd": "0702",
            "skey": "",
            "sval": "",
            "site_dvs": "",
            "ntt_tag": "",
        }
        self.max_pages = pages
        self.fields = fields or ["제목", "작성일", "조회수", "링크", "본문"]
        self.category = category

    @staticmethod
    def delay():
        time.sleep(random.uniform(2, 5))  # 딜레이 시간 증가

    def fetch_page(self, page: int) -> str:
        self.delay()
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        }
        self.params["GotoPage"] = page

        # 재시도 로직 추가
        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = requests.get(
                    self.base_url,
                    headers=headers,
                    params=self.params,
                    timeout=30  # 타임아웃 30초로 증가
                )
                res.encoding = 'utf-8'
                res.raise_for_status()
                return res.text
            except requests.Timeout:
                print(f"페이지 {page} 타임아웃 (시도 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(5)  # 재시도 전 5초 대기
                    continue
            except requests.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue

        print(f"페이지 {page} 가져오기 실패 (모든 재시도 소진)")
        return ""

    def parse_page(self, html: str) -> List[Dict]:
        if not html.strip():
            return []

        soup = BeautifulSoup(html, "html.parser")
        titles = soup.find_all("td", class_="title")
        hits = soup.find_all("td", class_="hits")
        dates = soup.find_all("td", class_="date")

        rows = []
        for idx, title_td in enumerate(titles):
            # 링크 추출
            a_tag = title_td.find("a")
            href = a_tag["href"] if a_tag and "href" in a_tag.attrs else ""
            full_url = urljoin(self.base_url, href)

            row = {}
            if self.category is not None:
                row["category"] = self.category
            if "제목" in self.fields:
                row["제목"] = title_td.get_text(strip=True)
            if "조회수" in self.fields and idx < len(hits):
                row["조회수"] = hits[idx].get_text(strip=True)
            if "작성일" in self.fields and idx < len(dates):
                row["작성일"] = dates[idx].get_text(strip=True)
            if "링크" in self.fields:
                row["링크"] = full_url

            rows.append(row)
        return rows

    def fetch_post_detail(self, url: str) -> str:
        self.delay()

        # 재시도 로직 추가
        max_retries = 2  # 본문은 2번만 재시도
        for attempt in range(max_retries):
            try:
                res = requests.get(url, timeout=30)  # 타임아웃 30초로 증가
                res.encoding = 'utf-8'
                res.raise_for_status()
                soup = BeautifulSoup(res.text, "html.parser")
                detail_div = soup.find("div", class_="board_viewDetail")
                return detail_div.get_text(strip=True) if detail_div else ""
            except requests.Timeout:
                print(f"본문 가져오기 타임아웃: {url} (시도 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(10)  # 재시도 전 10초 대기
                    continue
            except requests.RequestException as e:
                print(f"Error fetching post detail from {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue

        print(f"본문 가져오기 실패: {url}")
        return ""

    def crawl_all(self) -> List[Dict]:
        all_data = []
        for page in range(1, self.max_pages + 1):
            print(f"페이지 {page}/{self.max_pages} 크롤링 중...")
            html = self.fetch_page(page)
            parsed = self.parse_page(html)

            # 본문 필드가 필요하면 순차 크롤링
            if "본문" in self.fields:
                for i, row in enumerate(parsed):
                    print(f"  본문 {i + 1}/{len(parsed)} 가져오는 중...")
                    link = row.get("링크", "")
                    row["본문"] = self.fetch_post_detail(link) if link else ""

            all_data.extend(parsed)
            print(f"페이지 {page} 완료: {len(parsed)}개 데이터 수집")

        return all_data

    @staticmethod
    def save_to_csv(data: List[Dict]):
        # 수집된 데이터를 CSV 파일로 저장 (고정 파일명)
        if not data:
            print("저장할 데이터가 없습니다.")
            return

        filename = "cnu_board_data.csv"
        with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        print(f"{filename}에 저장되었습니다.")