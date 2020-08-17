from crawler.spiders import SpiderTemplate


class MextSpider(SpiderTemplate):
    name = 'mext'  # 文部科学省
    domain = 'mext.go.jp'
    start_urls = ['https://www.mext.go.jp/b_menu/houan/an/detail/mext_00004.html']
