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
