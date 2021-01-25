from crawler.spiders import TableSpiderTemplate


class MlitSpider(TableSpiderTemplate):
    name = 'mlit'  # 国土交通省
    domain = 'mlit.go.jp'
    start_urls = ['https://www.mlit.go.jp/policy/file000003.html#201']

    table_idx = 0
    bill_col = 1
    url_col = 3

    @staticmethod
    def build_start_url(diet_number):
        return f'https://www.mlit.go.jp/policy/file000003.html#{diet_number}'
