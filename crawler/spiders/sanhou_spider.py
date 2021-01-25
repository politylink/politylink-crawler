from crawler.spiders import DietTableSpiderTemplate


class SanhouSpider(DietTableSpiderTemplate):
    name = 'sanhou'  # 参議院法制局
    domain = 'sangiin.go.jp'

    table_idx = 1
    bill_col = 1
    url_col = 3

    @staticmethod
    def build_start_url(diet_number):
        return f'https://houseikyoku.sangiin.go.jp/sanhouichiran/kaijibetu/r-{diet_number}.htm'
