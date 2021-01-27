from crawler.spiders import TableSpiderTemplate


class CaoSpider(TableSpiderTemplate):
    name = 'caa'  # 消費者庁
    domain = 'caa.go.jp'
    bill_category = 'KAKUHOU'

    table_idx = 0
    bill_col = 1
    url_col = 2

    start_urls = ['https://www.caa.go.jp/law/bills/']
