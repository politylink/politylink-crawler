from crawler.spiders import SpiderTemplate


class MaffSpider(SpiderTemplate):
    name = 'maff'  # 農林水産省
    domain = 'maff.go.jp'
    start_urls = ['https://www.maff.go.jp/j/law/bill/201/index.html']
