from crawler.spiders import SpiderTemplate


class MofSpider(SpiderTemplate):
    name = 'mof'  # 財務省
    domain = 'mof.go.jp'
    start_urls = ['https://www.mof.go.jp/about_mof/bills/201diet/index.htm']
