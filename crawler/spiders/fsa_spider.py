from crawler.spiders import SpiderTemplate
from crawler.utils import build_url


class FsaSpider(SpiderTemplate):
    name = 'fsa'  # 金融庁
    domain = 'fsa.go.jp'
    start_urls = ['https://www.fsa.go.jp/common/diet/index.html']

    def parse(self, response):
        self.store_urls(
            [
                build_url(
                    href='https://www.fsa.go.jp/common/diet/201/02/gaiyou.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='https://www.fsa.go.jp/common/diet/201/02/shinkyuu.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '金融機能の強化のための特別措置に関する法律の一部を改正する法律案'
        )
        self.store_urls(
            [
                build_url(
                    href='https://www.fsa.go.jp/common/diet/201/01/gaiyou.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='https://www.fsa.go.jp/common/diet/201/01/shinkyuu.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '金融サービスの利用者の利便の向上及び保護を図るための金融商品の販売等に関する法律等の一部を改正する法律案'
        )
