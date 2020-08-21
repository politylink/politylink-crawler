from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class CaaSpider(ManualSpiderTemplate):
    name = 'caa'  # 消費者庁
    domain = 'caa.go.jp'
    start_urls = ['https://www.caa.go.jp/law/bills/']

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '公益通報者保護法の一部を改正する法律案',
         'href': 'https://www.caa.go.jp/law/bills/pdf/consumer_system_cms101_200306_01.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '公益通報者保護法の一部を改正する法律案',
         'href': 'https://www.caa.go.jp/law/bills/pdf/consumer_system_cms101_200306_04.pdf'},
    ]
