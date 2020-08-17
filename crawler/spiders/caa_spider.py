from crawler.spiders import SpiderTemplate
from crawler.utils import build_url


class CaaSpider(SpiderTemplate):
    name = 'caa'  # 消費者庁
    domain = 'caa.go.jp'
    start_urls = ['https://www.caa.go.jp/law/bills/']

    def parse(self, response):
        self.store_urls(
            [
                build_url(
                    href='https://www.caa.go.jp/law/bills/pdf/consumer_system_cms101_200306_01.pdf',
                    title='概要PDF',
                    domain=self.domain
                ),
                build_url(
                    href='https://www.caa.go.jp/law/bills/pdf/consumer_system_cms101_200306_04.pdf',
                    title='新旧対照表PDF',
                    domain=self.domain
                )
            ],
            '公益通報者保護法の一部を改正する法律案'
        )
