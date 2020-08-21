from crawler.spiders import TableSpiderTemplate, ManualSpiderTemplate
from crawler.utils import UrlTitle


class SoumuSpider(TableSpiderTemplate, ManualSpiderTemplate):
    name = 'soumu'  # 総務省
    domain = 'soumu.go.jp'
    start_urls = ['https://www.soumu.go.jp/menu_hourei/k_houan.html']

    table_idx = 0
    bill_col = 1
    url_col = 2

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '第201回国会閣法第55号',
         'href': 'https://www.soumu.go.jp/main_content/000685039.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '第201回国会閣法第55号',
         'href': 'https://www.soumu.go.jp/main_content/000685043.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '第201回国会閣法第6号',
         'href': 'https://www.soumu.go.jp/main_content/000667524.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '第201回国会閣法第6号',
         'href': 'https://www.soumu.go.jp/main_content/000667527.pdf'},
    ]

    def parse(self, response):
        self.parse_table(response)
        self.parse_items()
