import logging

import scrapy
from politylink.graphql.client import GraphQLClient
from politylink.graphql.schema import BillCategory, Bill


class BillSpider(scrapy.Spider):
    name = "bill"
    start_urls = ['http://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/menu.htm']

    def __init__(self, *args, **kwargs):
        super(BillSpider, self).__init__(*args, **kwargs)
        self.client = GraphQLClient()

    def parse(self, response):
        tables = response.xpath('//table')
        bills = self.parse_bill_table(tables[0], BillCategory.SYUHOU) + \
                self.parse_bill_table(tables[1], BillCategory.SANHOU) + \
                self.parse_bill_table(tables[1], BillCategory.KAKUHOU)
        self.log(f'scraped {len(bills)} bills')

        for bill in bills:
            self.client.exec_merge_bill(bill)
            self.log(f'inserted {bill.id}')

    def parse_bill_table(self, table, bill_category):
        bills = []
        for row in table.xpath('./tr')[1:]:  # skip header
            try:
                diet_number = int(row.xpath('./td[@headers="GIAN.KAIJI"]/span/text()').get())
                bill_number = int(row.xpath('./td[@headers="GIAN.NUMBER"]/span/text()').get())
                bill_title = row.xpath('./td[@headers="GIAN.KENMEI"]/span/text()').get()
            except Exception as e:
                self.log(f'failed to instantiate parse row:\n{row.get()}\n{e}', level=logging.ERROR)
                continue
            bills.append(self.build_bill(diet_number, bill_category, bill_number, bill_title))
        return bills

    @staticmethod
    def build_bill(diet_number, bill_category, bill_number, bill_title):
        bill = Bill(None)
        bill.id = f'bill:{diet_number}-{bill_category}-{bill_number}'
        bill.bill_category = bill_category
        bill.bill_number = bill_number
        bill.bill_title = bill_title
        return bill
