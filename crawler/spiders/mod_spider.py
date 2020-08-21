from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class ModSpider(ManualSpiderTemplate):
    name = 'mod'  # 防衛省
    domain = 'mod.go.jp'
    start_urls = ['https://www.mod.go.jp/j/presiding/houan/index.html']

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '防衛省設置法の一部を改正する法律案',
         'href': 'https://www.mod.go.jp/j/presiding/houan/pdf/201_200131/01.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '防衛省設置法の一部を改正する法律案',
         'href': 'https://www.mod.go.jp/j/presiding/houan/pdf/201_200131/04.pdf'},
    ]
