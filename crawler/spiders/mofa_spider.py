from crawler.spiders import TableSpiderTemplate


class MofaSpider(TableSpiderTemplate):
    name = 'mofa'  # 外務省
    domain = 'mofa.go.jp'
    bill_category = 'KAKUHOU'

    table_idx = 0
    bill_col = 1
    url_col = 2

    start_urls = ['https://www.mofa.go.jp/mofaj/ms/m_c/page24_001170.html']  # 第201回
