from crawler.spiders import SpiderTemplate
from crawler.utils import build_url


class NpaSpider(SpiderTemplate):
    name = 'npa'  # 警察庁
    domain = 'npa.go.jp'
    start_urls = ['https://www.npa.go.jp/laws/kokkai/index.html']

    def parse(self, response):
        self.store_urls(
            [
                build_url(
                    href='https://www.npa.go.jp/laws/kokkai/200303/gaiyou.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='https://www.npa.go.jp/laws/kokkai/200303/sinkyu.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '道路交通法の一部を改正する法律案'
        )
