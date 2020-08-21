from crawler.spiders import TableSpiderTemplate


class SanhouSpider(TableSpiderTemplate):
    name = 'sanhou'  # 参議院法制局
    domain = 'sangiin.go.jp'
    start_urls = ['https://houseikyoku.sangiin.go.jp/sanhouichiran/kaijibetu/r-201.htm']

    table_idx = 1
    bill_col = 1
    url_col = 3
