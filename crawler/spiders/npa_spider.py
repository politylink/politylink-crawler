import logging

from crawler.spiders import SpiderTemplate


class NpaSpider(SpiderTemplate):
    name = 'npa'  # 警察庁
    domain = 'npa.go.jp'
    start_urls = ['https://www.npa.go.jp/laws/kokkai/index.html']
