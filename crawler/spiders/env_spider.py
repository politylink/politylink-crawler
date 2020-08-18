from crawler.spiders import SpiderTemplate
from crawler.utils import build_url


class EnvSpider(SpiderTemplate):
    name = 'env'  # 環境省
    domain = 'env.go.jp'
    start_urls = ['http://www.env.go.jp/info/hoan/index.html']

    def parse(self, response):
        self.store_urls(
            [
                build_url(
                    href='http://www.env.go.jp/press/107831.html',
                    title='概要',
                    domain=self.domain
                ),
                build_url(
                    href='http://www.env.go.jp/press/107831/113496.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='http://www.env.go.jp/press/107831/113499.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '大気汚染防止法の一部を改正する法律案'
        )
