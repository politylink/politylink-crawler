from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class MetiSpider(ManualSpiderTemplate):
    name = 'meti'  # 経済産業省
    domain = 'meti.go.jp'
    start_urls = ['https://www.meti.go.jp/press/2019/02/20200218002/20200218002.html']

    items = [
        {'title': UrlTitle.GAIYOU,
         'bill_text': '特定高度情報通信技術活用システムの開発供給及び導入の促進に関する法律案',
         'href': 'https://www.meti.go.jp/press/2019/02/20200218002/20200218002.html'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '特定高度情報通信技術活用システムの開発供給及び導入の促進に関する法律案',
         'href': 'https://www.meti.go.jp/press/2019/02/20200218002/20200218002-4.pdf'},
        {'title': UrlTitle.GAIYOU,
         'bill_text': '特定デジタルプラットフォームの透明性及び公正性の向上に関する法律案',
         'href': 'https://www.meti.go.jp/press/2019/02/20200218001/20200218001.html'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '特定デジタルプラットフォームの透明性及び公正性の向上に関する法律案',
         'href': 'https://www.meti.go.jp/press/2019/02/20200218001/20200218001-1.pdf'},
        {'title': UrlTitle.GAIYOU,
         'bill_text': '強靱かつ持続可能な電気供給体制の確立を図るための電気事業法等の一部を改正する法律案',
         'href': 'https://www.meti.go.jp/press/2019/02/20200225001/20200225001.html'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '強靱かつ持続可能な電気供給体制の確立を図るための電気事業法等の一部を改正する法律案',
         'href': 'https://www.meti.go.jp/press/2019/02/20200225001/20200225001-5.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '強靱かつ持続可能な電気供給体制の確立を図るための電気事業法等の一部を改正する法律案',
         'href': 'https://www.meti.go.jp/press/2019/02/20200225001/20200225001-3.pdf'},
        {'title': UrlTitle.GAIYOU,
         'bill_text': '割賦販売法の一部を改正する法律案',
         'href': 'https://www.meti.go.jp/press/2019/03/20200303001/20200303001.html'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '割賦販売法の一部を改正する法律案',
         'href': 'https://www.meti.go.jp/press/2019/03/20200303001/20200303001-5.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '割賦販売法の一部を改正する法律案',
         'href': 'https://www.meti.go.jp/press/2019/03/20200303001/20200303001-3.pdf'},
        {'title': UrlTitle.GAIYOU,
         'bill_text': '中小企業の事業承継の促進のための中小企業における経営の承継の円滑化に関する法律等の一部を改正する法律案',
         'href': 'https://www.meti.go.jp/press/2019/03/20200310001/20200310001.html'},
        {'title': UrlTitle.GAIYOU_PDF,
         'bill_text': '中小企業の事業承継の促進のための中小企業における経営の承継の円滑化に関する法律等の一部を改正する法律案',
         'href': 'https://www.meti.go.jp/press/2019/03/20200310001/20200310001-5.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill_text': '中小企業の事業承継の促進のための中小企業における経営の承継の円滑化に関する法律等の一部を改正する法律案',
         'href': 'https://www.meti.go.jp/press/2019/03/20200310001/20200310001-3.pdf'},
    ]
