from crawler.spiders import SpiderTemplate


class CasSpider(SpiderTemplate):
    name = 'cas'  # 内閣官房
    domain = 'cas.go.jp'
    start_urls = ['http://www.cas.go.jp/jp/houan/201.html']
