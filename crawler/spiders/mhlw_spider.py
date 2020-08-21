from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class MhlwSpider(ManualSpiderTemplate):
    name = 'mhlw'  # 厚生労働省
    domain = 'mhlw.go.jp'
    start_urls = ['https://www.mhlw.go.jp/stf/topics/bukyoku/soumu/houritu/201.html']

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '労働基準法の一部を改正する法律案',
         'href': 'https://www.mhlw.go.jp/content/000591650.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '労働基準法の一部を改正する法律案',
         'href': 'https://www.mhlw.go.jp/content/000591653.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '雇用保険法等の一部を改正する法律案',
         'href': 'https://www.mhlw.go.jp/content/000591657.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '雇用保険法等の一部を改正する法律案',
         'href': 'https://www.mhlw.go.jp/content/000591661.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '年金制度の機能強化のための国民年金法等の一部を改正する法律案',
         'href': 'https://www.mhlw.go.jp/content/000601826.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '年金制度の機能強化のための国民年金法等の一部を改正する法律案',
         'href': 'https://www.mhlw.go.jp/content/000601829.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '地域共生社会の実現のための社会福祉法等の一部を改正する法律案',
         'href': 'https://www.mhlw.go.jp/content/000603796.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '地域共生社会の実現のための社会福祉法等の一部を改正する法律案',
         'href': 'https://www.mhlw.go.jp/content/000603799.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '新型コロナウイルス感染症等の影響に対応するための雇用保険法の臨時特例等に関する法律案',
         'href': 'https://www.mhlw.go.jp/content/000637670.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '新型コロナウイルス感染症等の影響に対応するための雇用保険法の臨時特例等に関する法律案',
         'href': 'https://www.mhlw.go.jp/content/000637678.pdf'},
    ]
