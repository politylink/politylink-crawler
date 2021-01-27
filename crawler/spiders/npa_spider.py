from crawler.spiders import TableSpiderTemplate


class NpaSpider(TableSpiderTemplate):
    name = 'npa'  # 警察庁
    domain = 'npa.go.jp'
    bill_category = 'KAKUHOU'

    table_idx = 0
    bill_col = 1
    url_col = 2

    start_urls = ['https://www.npa.go.jp/laws/kokkai/index.html']
