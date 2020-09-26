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

        aliases = []
        for i in range(1, 6):
            val = row[f'alias{i}']
            if val:
                aliases.append(val)
        if aliases:
            bill.aliases = aliases
            client.exec_merge_bill(bill)
            print(f'set alias={bill.aliases} for {bill.bill_number}')


if __name__ == '__main__':
    main('./data/alias.csv')
