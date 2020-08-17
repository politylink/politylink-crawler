from crawler.spiders import TableSpiderTemplate
from crawler.utils import build_url


class MofSpider(TableSpiderTemplate):
    name = 'mof'  # 財務省
    domain = 'mof.go.jp'
    start_urls = ['https://www.mof.go.jp/about_mof/bills/201diet/index.htm']

    table_idx = 0
    bill_col = 1
    url_col = 2

    def parse(self, response):
        super(MofSpider, self).parse(response)

        for bill_title, url_href in [
            (
                    '新型コロナウイルス感染症等の影響に対応するための国税関係法律の臨時特例に関する法律案',
                    'https://www.mof.go.jp/about_mof/bills/201diet/kz020427g.html'
            ), (
                    '株式会社日本政策投資銀行法の一部を改正する法律案',
                    'https://www.mof.go.jp/about_mof/bills/201diet/20200225g.htm'
            ), (
                    '国際金融公社への加盟に伴う措置に関する法律及び国際開発協会への加盟に伴う措置に関する法律の一部を改正する法律案',
                    'https://www.mof.go.jp/about_mof/bills/201diet/in20200204g.htm'
            ), (
                    '関税定率法等の一部を改正する法律案',
                    'https://www.mof.go.jp/about_mof/bills/201diet/ka20200204g.htm'
            ), (
                    '所得税法等の一部を改正する法律案',
                    'https://www.mof.go.jp/about_mof/bills/201diet/st020131g.htm'
            ), (
                    '平成30年度歳入歳出の決算上の剰余金の処理の特例に関する法律案',
                    'https://www.mof.go.jp/about_mof/bills/201diet/zk20200120g.htm'
            )
        ]:
            self.store_urls([build_url(url_href, title='概要', domain=self.domain)], bill_title)
