import scrapy

from politylink.graphql.client import GraphQLClient
from politylink.helpers import BillFinder


class SpiderTemplate(scrapy.Spider):
    def __init__(self, *args, **kwargs):
        super(SpiderTemplate, self).__init__(*args, **kwargs)
        self.client = GraphQLClient()
        self.bill_finder = BillFinder()

    def parse(self, response):
        NotImplemented

    def store_urls(self, urls, bill_title):
        bills = self.bill_finder.find(bill_title)
        for url in urls:
            self.client.exec_merge_url(url)
            for bill in bills:
                self.client.exec_merge_url_referred_bills(url.id, bill.id)
