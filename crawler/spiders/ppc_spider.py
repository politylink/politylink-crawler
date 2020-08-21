from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class PpcSpider(ManualSpiderTemplate):
    name = 'ppc'  # 個人情報保護委員会
    domain = 'ppc.go.jp'
    start_urls = ['https://www.ppc.go.jp/personalinfo/legal/html_kaiseihogohou/']

    items = [
        {'title': UrlTitle.GAIYOU,
         'bill_text': '個人情報の保護に関する法律等の一部を改正する法律案',
         'href': 'https://www.ppc.go.jp/personalinfo/legal/html_kaiseihogohou/'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '個人情報の保護に関する法律等の一部を改正する法律案',
         'href': 'https://www.ppc.go.jp/files/pdf/200612_gaiyou.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '個人情報の保護に関する法律等の一部を改正する法律案',
         'href': 'https://www.ppc.go.jp/files/pdf/200612_sinkyutaisyohyo.pdf'},
    ]
