from cnu_main_crawler import CnuMainCrawling

if __name__ == "__main__":
    crawler = CnuMainCrawling(code="sub07_0702", pages=1, category="학사정보")
    data = crawler.crawl_all()
    crawler.save_to_csv(data)

