from crawler.spiders import SpiderTemplate


class FsaSpider(SpiderTemplate):
    name = 'fsa'  # 金融庁
    domain = 'fsa.go.jp'
    start_urls = ['https://www.fsa.go.jp/common/diet/index.html']
