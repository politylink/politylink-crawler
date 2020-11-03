from logging import getLogger

from crawler.spiders import TableSpiderTemplate, ManualSpiderTemplate
from crawler.utils import UrlTitle

LOGGER = getLogger(__name__)


class CaoSpider(TableSpiderTemplate, ManualSpiderTemplate):
    name = 'cao'  # 内閣府
    domain = 'cao.go.jp'
    start_urls = ['https://www.cao.go.jp/houan/203/index.html']

    table_idx = 0
    bill_col = 0
    url_col = 3

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '第201回国会閣法第5号',
         'url': 'https://www.cao.go.jp/houan/doc/201_1gaiyou.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '第201回国会閣法第5号',
         'url': 'https://www.cao.go.jp/houan/doc/201_1shinkyu.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '第201回国会閣法第57号',
         'url': 'https://www.cao.go.jp/houan/pdf/201/201_4gaiyou.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '第201回国会閣法第57号',
         'url': 'https://www.cao.go.jp/houan/pdf/201/201_4shinkyu.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '第203回国会閣法第2号',
         'url': 'https://www.cao.go.jp/houan/pdf/203/203gaiyou.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '第203回国会閣法第2号',
         'url': 'https://www.cao.go.jp/houan/pdf/203/203shinkyu.pdf'},
        {'title': UrlTitle.PUBLIC_COMMENT,
         'bill': '第203回国会閣法第2号',
         'url': 'https://search.e-gov.go.jp/servlet/Public?CLASSNAME=PCMMSTDETAIL&id=095201040&Mode=0'},
    ]

    def parse(self, response):
        self.parse_table(response)
        self.parse_items()
