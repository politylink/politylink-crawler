from crawler.spiders import DietTableSpiderTemplate


class CaoSpider(DietTableSpiderTemplate):
    name = 'cao'  # 内閣府
    domain = 'cao.go.jp'

    table_idx = 0
    bill_col = 0
    url_col = 3

    @staticmethod
    def build_start_url(diet_number):
        return f'https://www.cao.go.jp/houan/{diet_number}/index.html'
