from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class EnvSpider(ManualSpiderTemplate):
    name = 'env'  # 環境省
    domain = 'env.go.jp'
    start_urls = ['http://www.env.go.jp/info/hoan/index.html']

    items = [
        {'title': UrlTitle.GAIYOU,
         'bill': '大気汚染防止法の一部を改正する法律案',
         'url': 'http://www.env.go.jp/press/107831.html'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '大気汚染防止法の一部を改正する法律案',
         'url': 'http://www.env.go.jp/press/107831/113496.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '大気汚染防止法の一部を改正する法律案',
         'url': 'http://www.env.go.jp/press/107831/113499.pdf'},
    ]
