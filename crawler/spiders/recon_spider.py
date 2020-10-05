from crawler.spiders import ManualSpiderTemplate
from crawler.utils import UrlTitle


class ReconstructionSpider(ManualSpiderTemplate):
    name = 'recon'  # 復興庁
    domain = 'recon.go.jp'
    start_urls = ['https://www.reconstruction.go.jp/topics/20200303085910.html']

    items = [
        {'title': UrlTitle.GAIYOU_PDF,
         'bill': '復興庁設置法等の一部を改正する法律案',
         'url': 'https://www.reconstruction.go.jp/topics/main-cat12/sub-cat12-1/200303gaiyou.pdf'},
        {'title': UrlTitle.SINKYU_PDF,
         'bill': '復興庁設置法等の一部を改正する法律案',
         'url': 'https://www.reconstruction.go.jp/topics/main-cat12/sub-cat12-1/200303sinkyu.pdf'},
    ]
