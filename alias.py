import pandas as pd

from politylink.graphql.client import GraphQLClient
from politylink.helpers import BillFinder


def main(fp):
    bill_finder = BillFinder()
    client = GraphQLClient()
    df = pd.read_csv(fp, names=['text', 'aliases'])
    for text, aliases in zip(df['text'], df['aliases']):
        bills = bill_finder.find(text)
        if len(bills) != 1:
            print(f'found {len(bills)} Bills for {text}')
            continue
        bill = bills[0]
        bill.aliases = aliases.split(';')
        client.exec_merge_bill(bill)
        print(f'set alias={bill.aliases} for {bill.bill_number}')


if __name__ == '__main__':
    main('./data/alias.csv')
