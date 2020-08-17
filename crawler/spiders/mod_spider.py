from crawler.spiders import SpiderTemplate


class ModSpider(SpiderTemplate):
    name = 'mod'  # 防衛省
    domain = 'mod.go.jp'
    start_urls = ['https://www.mod.go.jp/j/presiding/houan/index.html']
