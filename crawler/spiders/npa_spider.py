from crawler.spiders import TableSpiderTemplate


class NpaSpider(TableSpiderTemplate):
    name = 'npa'  # 警察庁
    domain = 'npa.go.jp'
    start_urls = ['https://www.npa.go.jp/laws/kokkai/index.html']

    table_idx = 0
    bill_col = 1
    url_col = 2
