from crawler.spiders import TableSpiderTemplate, ManualSpiderTemplate
from crawler.utils import UrlTitle


class MofSpider(TableSpiderTemplate, ManualSpiderTemplate):
    name = 'mof'  # 財務省
    domain = 'mof.go.jp'
    start_urls = ['https://www.mof.go.jp/about_mof/bills/201diet/index.htm']

    table_idx = 0
    bill_col = 1
    url_col = 2

    items = [
        {'title': UrlTitle.GAIYOU,
         'bill_text': '新型コロナウイルス感染症等の影響に対応するための国税関係法律の臨時特例に関する法律案',
         'href': 'https://www.mof.go.jp/about_mof/bills/201diet/kz020427g.html'},
        {'title': UrlTitle.GAIYOU,
         'bill_text': '株式会社日本政策投資銀行法の一部を改正する法律案',
         'href': 'https://www.mof.go.jp/about_mof/bills/201diet/20200225g.htm'},
        {'title': UrlTitle.GAIYOU,
         'bill_text': '国際金融公社への加盟に伴う措置に関する法律及び国際開発協会への加盟に伴う措置に関する法律の一部を改正する法律案',
         'href': 'https://www.mof.go.jp/about_mof/bills/201diet/in20200204g.htm'},
        {'title': UrlTitle.GAIYOU,
         'bill_text': '関税定率法等の一部を改正する法律案',
         'href': 'https://www.mof.go.jp/about_mof/bills/201diet/ka20200204g.htm'},
        {'title': UrlTitle.GAIYOU,
         'bill_text': '所得税法等の一部を改正する法律案',
         'href': 'https://www.mof.go.jp/about_mof/bills/201diet/st020131g.htm'},
        {'title': UrlTitle.GAIYOU,
         'bill_text': '平成三十年度歳入歳出の決算上の剰余金の処理の特例に関する法律案',
         'href': 'https://www.mof.go.jp/about_mof/bills/201diet/zk20200120g.htm'},
    ]

    def parse(self, response):
        self.parse_table(response)
        self.parse_items()
