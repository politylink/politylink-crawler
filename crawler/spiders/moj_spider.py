from crawler.spiders import SpiderTemplate
from crawler.utils import build_url


class MojSpider(SpiderTemplate):
    name = 'moj'  # 法務省
    domain = 'moj.go.jp'
    start_urls = ['http://www.moj.go.jp/hisho/kouhou/houan201.html']

    def parse(self, response):
        self.store_urls(
            [
                build_url(
                    href='http://www.moj.go.jp/content/001313627.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '裁判所職員定員法の一部を改正する法律案'
        )
        self.store_urls(
            [
                build_url(
                    href='http://www.moj.go.jp/content/001316234.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '自動車の運転により人を死傷させる行為等の処罰に関する法律の一部を改正する法律案'
        )