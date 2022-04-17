from crawler.spiders import TableSpiderTemplate


class SoumuSpider(TableSpiderTemplate):
    name = 'soumu'  # 総務省
    domain = 'soumu.go.jp'
    bill_category = 'KAKUHOU'
    diet_number = 208

    table_idx = 0
    bill_col = 1
    url_col = 2

    start_urls = ['https://www.soumu.go.jp/menu_hourei/k_houan.html']
