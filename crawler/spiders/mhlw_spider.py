from crawler.spiders import SpiderTemplate


class CasSpider(SpiderTemplate):
    name = 'mhlw'  # 厚生労働省
    domain = 'mhlw.go.jp'
    start_urls = ['https://www.mhlw.go.jp/stf/topics/bukyoku/soumu/houritu/201.html']
