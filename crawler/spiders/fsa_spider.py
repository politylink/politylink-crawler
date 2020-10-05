from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class FsaSpider(ManualSpiderTemplate):
    name = 'fsa'  # 金融庁
    domain = 'fsa.go.jp'
    start_urls = ['https://www.fsa.go.jp/common/diet/index.html']

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '金融機能の強化のための特別措置に関する法律の一部を改正する法律案',
         'url': 'https://www.fsa.go.jp/common/diet/201/02/gaiyou.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '金融機能の強化のための特別措置に関する法律の一部を改正する法律案',
         'url': 'https://www.fsa.go.jp/common/diet/201/02/shinkyuu.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '金融サービスの利用者の利便の向上及び保護を図るための金融商品の販売等に関する法律等の一部を改正する法律案',
         'url': 'https://www.fsa.go.jp/common/diet/201/01/gaiyou.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '金融サービスの利用者の利便の向上及び保護を図るための金融商品の販売等に関する法律等の一部を改正する法律案',
         'url': 'https://www.fsa.go.jp/common/diet/201/01/shinkyuu.pdf'},
    ]
