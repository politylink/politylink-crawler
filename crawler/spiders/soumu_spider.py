from crawler.spiders import TableSpiderTemplate, ManualSpiderTemplate


class SoumuSpider(TableSpiderTemplate, ManualSpiderTemplate):
    name = 'soumu'  # 総務省
    domain = 'soumu.go.jp'
    start_urls = ['https://www.soumu.go.jp/menu_hourei/k_houan.html']

    table_idx = 0
    bill_col = 1
    url_col = 2

    @staticmethod
    def build_start_url(diet_number):
        return 'https://www.soumu.go.jp/menu_hourei/k_houan.html'
