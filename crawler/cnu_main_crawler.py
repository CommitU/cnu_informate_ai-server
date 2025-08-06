import csv
import time
import random
import requests
from bs4 import BeautifulSoup

class CnuMainCrawling:
    def __init__(self, code, pages):
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

    @staticmethod
    def delay():
        sleep_time = random.uniform(1, 2.5)
        time.sleep(sleep_time)

    def fetch_page(self, page: int) -> str:
        # 주어진 페이지의 HTML을 반환
        self.delay()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }

        self.params["GotoPage"] = page
        res = requests.get(self.base_url, headers=headers, params=self.params)
        res.encoding = 'utf-8'
        res.raise_for_status()
        return res.text

    def parse_titles(self, html: str) -> list:
        # HTML에서 게시글 제목 추출
        soup = BeautifulSoup(html, "html.parser")
        titles = soup.find_all("td", class_="title")
        return [title.text.strip() for title in titles]

    def parse_hits(self, html: str) -> list:
        # HTML에서 조회수 추출
        soup = BeautifulSoup(html, "html.parser")
        hits = soup.find_all("td", class_="hits")
        return [hit.text.strip() for hit in hits]

    def parse_dates(self, html: str) -> list:
        # HTML에서 날짜 추출
        soup = BeautifulSoup(html, "html.parser")
        dates = soup.find_all("td", class_="date")
        return [date.text.strip() for date in dates]

    def parse_post_links(self, html: str) -> list:
        # HTML에서 상세 페이지 링크 추출
        soup = BeautifulSoup(html, "html.parser")
        titles = soup.find_all("td", class_="title")
        links = []
        for title in titles:
            a_tag = title.find("a")
            if a_tag and 'href' in a_tag.attrs:
                href = a_tag['href']
                full_url = requests.compat.urljoin(self.base_url, href)
                links.append(full_url)
        return links

    def fetch_post_detail(self, url: str) -> str:
        # 상세 페이지에서 게시글 본문을 추출
        self.delay()
        res = requests.get(url)
        res.encoding = 'utf-8'
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        detail_div = soup.find("div", class_="board_viewDetail")
        return detail_div.get_text(strip=True) if detail_div else ""

    def crawl_all(self):
        # 1페이지부터 max_pages까지 크롤링
        for page in range(1, self.max_pages + 1):
            all_data = []

            html = self.fetch_page(page)
            titles = self.parse_titles(html)
            hits = self.parse_hits(html)
            dates = self.parse_dates(html)
            links = self.parse_post_links(html)

            for title, date, hit, link in zip(titles, dates, hits, links):
                contents = self.fetch_post_detail(link)
                all_data.append({
                    "제목": title,
                    "작성일": date,
                    "조회수": hit,
                    "링크": link,
                    "본문": contents
                })
        return all_data

    def save_to_csv(self, data: list[dict], output_file: str = "cnu_board_data.csv"):
        # 수집된 데이터를 CSV 파일로 저장
        if not data:
            print("저장할 데이터가 없던데...?")
            return

        with open(output_file, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            for row in data:
                writer.writerow(row)

        print(f"{output_file}에 저장 완력되었습니다.ㅇ")