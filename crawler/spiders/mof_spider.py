from crawler.spiders import DietTableSpiderTemplate


class MofSpider(DietTableSpiderTemplate):
    name = 'mof'  # 財務省
    domain = 'mof.go.jp'
    bill_category = 'KAKUHOU'

    table_idx = 0
    bill_col = 1
    url_col = 2

    @staticmethod
    def build_start_url(diet_number):
        return f'https://www.mof.go.jp/about_mof/bills/{diet_number}diet/index.htm'
