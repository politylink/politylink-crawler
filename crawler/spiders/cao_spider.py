from crawler.spiders import SpiderTemplate


class CaoSpider(SpiderTemplate):
    name = 'cao'  # 内閣府
    domain = 'cao.go.jp'
    start_urls = ['https://www.cao.go.jp/houan/201/index.html']
