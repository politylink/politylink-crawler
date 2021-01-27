from crawler.spiders import DietTableSpiderTemplate


class MaffSpider(DietTableSpiderTemplate):
    name = 'maff'  # 農林水産省
    domain = 'maff.go.jp'
    bill_category = 'KAKUHOU'

    table_idx = 0
    bill_col = 1
    url_col = 2

    @staticmethod
    def build_start_url(diet_number):
        return f'https://www.maff.go.jp/j/law/bill/{diet_number}/index.html'
