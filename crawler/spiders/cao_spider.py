from logging import getLogger

from crawler.spiders import TableSpiderTemplate

LOGGER = getLogger(__name__)


class CaoSpider(TableSpiderTemplate):
    name = 'cao'  # 内閣府
    domain = 'cao.go.jp'
    start_urls = ['https://www.cao.go.jp/houan/201/index.html']

    table_idx = 0
    bill_col = 0
    url_col = 3
