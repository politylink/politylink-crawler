from crawler.spiders import DietTableSpiderTemplate


class CasSpider(DietTableSpiderTemplate):
    name = 'cas'  # 内閣官房
    domain = 'cas.go.jp'

    table_idx = 1
    bill_col = 0
    url_col = 3

    @staticmethod
    def build_start_url(diet_number):
        return f'http://www.cas.go.jp/jp/houan/{diet_number}.html'
