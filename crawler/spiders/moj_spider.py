from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class MojSpider(ManualSpiderTemplate):
    name = 'moj'  # 法務省
    domain = 'moj.go.jp'
    start_urls = ['http://www.moj.go.jp/hisho/kouhou/houan201.html']

    items = [
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '裁判所職員定員法の一部を改正する法律案',
         'url': 'http://www.moj.go.jp/content/001313627.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '自動車の運転により人を死傷させる行為等の処罰に関する法律の一部を改正する法律案',
         'url': 'http://www.moj.go.jp/content/001316234.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '外国弁護士による法律事務の取扱いに関する特別措置法の一部を改正する法律案',
         'url': 'http://www.moj.go.jp/content/001308756.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '外国弁護士による法律事務の取扱いに関する特別措置法の一部を改正する法律案',
         'url': 'http://www.moj.go.jp/content/001308064.pdf'},
    ]
