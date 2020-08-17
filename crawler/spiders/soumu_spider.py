from crawler.spiders import SpiderTemplate


class SoumuSpider(SpiderTemplate):
    name = 'soumu'  # 総務省
    domain = 'soumu.go.jp'
    start_urls = ['https://www.soumu.go.jp/menu_hourei/k_houan.html']
