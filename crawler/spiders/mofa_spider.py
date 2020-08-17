from crawler.spiders import SpiderTemplate


class MofaSpider(SpiderTemplate):
    name = 'mofa'  # 外務省
    domain = 'cas.go.jp'
    start_urls = ['https://www.mofa.go.jp/mofaj/ms/m_c/page24_001170.html']
