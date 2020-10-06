from crawler.spiders import TableSpiderTemplate, ManualSpiderTemplate
from crawler.utils import UrlTitle


class CasSpider(TableSpiderTemplate, ManualSpiderTemplate):
    name = 'cas'  # 内閣官房
    domain = 'cas.go.jp'
    start_urls = ['http://www.cas.go.jp/jp/houan/201.html']

    table_idx = 1
    bill_col = 0
    url_col = 3

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '第201回国会閣法第52号',
         'url': 'http://www.cas.go.jp/jp/houan/200313/siryou1.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '第201回国会閣法第52号',
         'url': 'http://www.cas.go.jp/jp/houan/200313/siryou4.pdf'},
    ]

    def parse(self, response):
        self.parse_table(response)
        self.parse_items()
