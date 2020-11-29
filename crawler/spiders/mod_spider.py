from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class ModSpider(ManualSpiderTemplate):
    name = 'mod'  # 防衛省
    domain = 'mod.go.jp'
    start_urls = ['https://www.mod.go.jp/j/presiding/houan/index.html']

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '防衛省設置法の一部を改正する法律案',
         'url': 'https://www.mod.go.jp/j/presiding/houan/pdf/201_200131/01.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '防衛省設置法の一部を改正する法律案',
         'url': 'https://www.mod.go.jp/j/presiding/houan/pdf/201_200131/04.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '第203回国会閣法第7号',
         'url': 'https://www.mod.go.jp/j/presiding/houan/pdf/203_201106/01.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '第203回国会閣法第7号',
         'url': 'https://www.mod.go.jp/j/presiding/houan/pdf/203_201106/04.pdf'},
    ]
