from crawler.spiders import SpiderTemplate


class MojSpider(SpiderTemplate):
    name = 'moj'  # 法務省
    domain = 'moj.go.jp'
    start_urls = ['http://www.moj.go.jp/hisho/kouhou/houan201.html']
