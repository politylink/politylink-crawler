from crawler.spiders import SpiderTemplate
from crawler.utils import build_url


class MhlwSpider(SpiderTemplate):
    name = 'mhlw'  # 厚生労働省
    domain = 'mhlw.go.jp'
    start_urls = ['https://www.mhlw.go.jp/stf/topics/bukyoku/soumu/houritu/201.html']

    def parse(self, response):
        self.store_urls(
            [
                build_url(
                    href='https://www.mhlw.go.jp/content/000591650.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='https://www.mhlw.go.jp/content/000591653.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '労働基準法の一部を改正する法律案'
        )
        self.store_urls(
            [
                build_url(
                    href='https://www.mhlw.go.jp/content/000591657.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='https://www.mhlw.go.jp/content/000591661.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '雇用保険法等の一部を改正する法律案'
        )
        self.store_urls(
            [
                build_url(
                    href='https://www.mhlw.go.jp/content/000601826.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='https://www.mhlw.go.jp/content/000601829.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '年金制度の機能強化のための国民年金法等の一部を改正する法律案'
        )
        self.store_urls(
            [
                build_url(
                    href='https://www.mhlw.go.jp/content/000603796.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='https://www.mhlw.go.jp/content/000603799.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '地域共生社会の実現のための社会福祉法等の一部を改正する法律案'
        )
        self.store_urls(
            [
                build_url(
                    href='https://www.mhlw.go.jp/content/000637670.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='https://www.mhlw.go.jp/content/000637678.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '新型コロナウイルス感染症等の影響に対応するための雇用保険法の臨時特例等に関する法律案'
        )
