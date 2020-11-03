from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class MhlwSpider(ManualSpiderTemplate):
    name = 'mhlw'  # 厚生労働省
    domain = 'mhlw.go.jp'
    start_urls = ['https://www.mhlw.go.jp/stf/topics/bukyoku/soumu/houritu/201.html']

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '労働基準法の一部を改正する法律案',
         'url': 'https://www.mhlw.go.jp/content/000591650.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '労働基準法の一部を改正する法律案',
         'url': 'https://www.mhlw.go.jp/content/000591653.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '雇用保険法等の一部を改正する法律案',
         'url': 'https://www.mhlw.go.jp/content/000591657.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '雇用保険法等の一部を改正する法律案',
         'url': 'https://www.mhlw.go.jp/content/000591661.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '年金制度の機能強化のための国民年金法等の一部を改正する法律案',
         'url': 'https://www.mhlw.go.jp/content/000601826.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '年金制度の機能強化のための国民年金法等の一部を改正する法律案',
         'url': 'https://www.mhlw.go.jp/content/000601829.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '地域共生社会の実現のための社会福祉法等の一部を改正する法律案',
         'url': 'https://www.mhlw.go.jp/content/000603796.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '地域共生社会の実現のための社会福祉法等の一部を改正する法律案',
         'url': 'https://www.mhlw.go.jp/content/000603799.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '新型コロナウイルス感染症等の影響に対応するための雇用保険法の臨時特例等に関する法律案',
         'url': 'https://www.mhlw.go.jp/content/000637670.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '新型コロナウイルス感染症等の影響に対応するための雇用保険法の臨時特例等に関する法律案',
         'url': 'https://www.mhlw.go.jp/content/000637678.pdf'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '予防接種法及び検疫法の一部を改正する法律案',
         'url': 'https://www.mhlw.go.jp/content/000686922.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '予防接種法及び検疫法の一部を改正する法律案',
         'url': 'https://www.mhlw.go.jp/content/000686925.pdf'},
    ]
