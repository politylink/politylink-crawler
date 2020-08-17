from crawler.spiders import SpiderTemplate


class CaaSpider(SpiderTemplate):
    name = 'caa'  # 消費者庁
    domain = 'caa.go.jp'
    start_urls = ['https://www.caa.go.jp/law/bills/']
