from crawler.spiders import TableSpiderTemplate


class MaffSpider(TableSpiderTemplate):
    name = 'maff'  # 農林水産省
    domain = 'maff.go.jp'
    start_urls = ['https://www.maff.go.jp/j/law/bill/201/index.html']

    table_idx = 0
    bill_col = 1
    url_col = 2
