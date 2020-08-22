import pandas as pd

from politylink.graphql.client import GraphQLClient
from politylink.helpers import BillFinder


def main(fp):
    bill_finder = BillFinder()
    client = GraphQLClient()
    df = pd.read_csv(fp)
    for bill_text, bill_alias in zip(df['bill_text'], df['bill_alias']):
        bills = bill_finder.find(bill_text)
        if len(bills) == 1:
            bill = bills[0]
            bill.alias = bill_alias
            client.exec_merge_bill(bill)
            print(f'set alias={bill_alias} for {bill.bill_number}')
        else:
            print(f'found {len(bills)} Bills for {bill_text}')


if __name__ == '__main__':
    main('./data/alias.csv')
