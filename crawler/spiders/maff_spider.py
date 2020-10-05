from crawler.spiders import TableSpiderTemplate, ManualSpiderTemplate
from crawler.utils import UrlTitle


class MaffSpider(TableSpiderTemplate, ManualSpiderTemplate):
    name = 'maff'  # 農林水産省
    domain = 'maff.go.jp'
    start_urls = ['https://www.maff.go.jp/j/law/bill/201/index.html']

    table_idx = 0
    bill_col = 1
    url_col = 2

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '第201回国会閣法第25号',
         'url': 'https://www.maff.go.jp/j/law/bill/201/attach/pdf/index-13.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '第201回国会閣法第25号',
         'url': 'https://www.maff.go.jp/j/law/bill/201/attach/pdf/index-11.pdf'},
    ]

    def parse(self, response):
        self.parse_table(response)
        self.parse_items()
