from crawler.spiders import TableSpiderTemplate


class MlitSpider(TableSpiderTemplate):
    name = 'mlit'  # 国土交通省
    domain = 'mlit.go.jp'
    bill_category = 'KAKUHOU'

    table_idx = 0
    bill_col = 1
    url_col = 3

    start_urls = ['https://www.mlit.go.jp/policy/file000003.html']
