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