from crawler.spiders import TableSpiderTemplate, ManualSpiderTemplate
from crawler.utils import UrlTitle


class ShuhouSpider(TableSpiderTemplate, ManualSpiderTemplate):
    name = 'shuhou'  # 衆議院法制局
    domain = 'shugiin.go.jp'
    start_urls = ['http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/housei/html/h-shuhou201.html']

    table_idx = 0
    bill_col = 1
    url_col = 5

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '第201回国会衆法第2号',
         'href': 'http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/housei/pdf/201hou2siryou.pdf/$File/201hou2siryou.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '第201回国会衆法第2号',
         'href': 'http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/housei/pdf/201hou2sinkyu.pdf/$File/201hou2sinkyu.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '第201回国会衆法第8号',
         'href': 'http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/housei/pdf/201hou8sinkyu.pdf/$File/201hou8sinkyu.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '第201回国会衆法第11号',
         'href': 'http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/housei/pdf/201hou11siryou.pdf/$File/201hou11siryou.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '第201回国会衆法第11号',
         'href': 'http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/housei/pdf/201hou11sinkyu.pdf/$File/201hou11sinkyu.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '第201回国会衆法第16号',
         'href': 'http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/housei/pdf/201hou16siryou1.pdf/$File/201hou16siryou1.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '第201回国会衆法第16号',
         'href': 'http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/housei/pdf/201hou16sinkyu.pdf/$File/201hou16sinkyu.pdf'},
    ]

    def parse(self, response):
        self.parse_table(response)
        self.parse_items()
