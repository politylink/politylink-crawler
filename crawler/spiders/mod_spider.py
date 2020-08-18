from crawler.spiders import SpiderTemplate
from crawler.utils import build_url


class ModSpider(SpiderTemplate):
    name = 'mod'  # 防衛省
    domain = 'mod.go.jp'
    start_urls = ['https://www.mod.go.jp/j/presiding/houan/index.html']

    def parse(self, response):
        self.store_urls(
            [
                build_url(
                    href='https://www.mod.go.jp/j/presiding/houan/pdf/201_200131/01.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='https://www.mod.go.jp/j/presiding/houan/pdf/201_200131/04.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '防衛省設置法の一部を改正する法律案'
        )