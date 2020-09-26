import pandas as pd

from politylink.graphql.client import GraphQLClient
from politylink.helpers import BillFinder


def main(fp):
    bill_finder = BillFinder()
    client = GraphQLClient()
    df = pd.read_csv(fp).fillna('')
    for _, row in df.iterrows():
        text = row['billNumber']
        bills = bill_finder.find(text)
        if len(bills) != 1:
            print(f'found {len(bills)} Bills for {text}')
            continue
        bill = bills[0]

        aliases = list(filter(lambda x: x, [row['alias1'], row['alias2'], row['alias3']]))
        tags = list(filter(lambda x: x, [row['tag1'], row['tag2'], row['tag3']]))
        bill.aliases = aliases
        bill.tags = tags
        client.exec_merge_bill(bill)
        print(f'set alias={bill.aliases} tags={bill.tags} for {bill.bill_number}')


if __name__ == '__main__':
    main('./data/alias.csv')
