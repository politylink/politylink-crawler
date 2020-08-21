from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class NpaSpider(ManualSpiderTemplate):
    name = 'npa'  # 警察庁
    domain = 'npa.go.jp'
    start_urls = ['https://www.npa.go.jp/laws/kokkai/index.html']

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '道路交通法の一部を改正する法律案',
         'href': 'https://www.npa.go.jp/laws/kokkai/200303/gaiyou.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '道路交通法の一部を改正する法律案',
         'href': 'https://www.npa.go.jp/laws/kokkai/200303/sinkyu.pdf'},
    ]
