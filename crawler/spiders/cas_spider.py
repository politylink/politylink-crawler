from crawler.spiders import TableSpiderTemplate


class CasSpider(TableSpiderTemplate):
    name = 'cas'  # 内閣官房
    domain = 'cas.go.jp'
    start_urls = ['http://www.cas.go.jp/jp/houan/201.html']

    table_idx = 1
    bill_col = 0
    url_col = 3
