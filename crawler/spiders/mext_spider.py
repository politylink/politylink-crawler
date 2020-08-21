from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class MextSpider(ManualSpiderTemplate):
    name = 'mext'  # 文部科学省
    domain = 'mext.go.jp'
    start_urls = ['https://www.mext.go.jp/b_menu/houan/an/detail/mext_00004.html']

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '文化観光拠点施設を中核とした地域における文化観光の推進に関する法律案',
         'href': 'https://www.mext.go.jp/content/20200422-mxt_hourei-000006827_1.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '文化観光拠点施設を中核とした地域における文化観光の推進に関する法律案',
         'href': 'https://www.mext.go.jp/content/20200422-mxt_hourei-000006827_3.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '著作権法及びプログラムの著作物に係る登録の特例に関する法律の一部を改正する法律案',
         'href': 'https://www.mext.go.jp/content/20200306-mxt_hourei-000005016_01.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '著作権法及びプログラムの著作物に係る登録の特例に関する法律の一部を改正する法律案',
         'href': 'https://www.mext.go.jp/content/20200306-mxt_hourei-000005016_05.pdf'},
    ]
