"""
Elasticsearchインスタンスを生成するためのbuildメソッドを定義する
"""

from politylink.elasticsearch.schema import BillText


def build_bill_text(bill_id, texts):
    supplement_idx = texts.index('附 則')
    reason_idx = texts.index('理 由')
    if supplement_idx > reason_idx:
        raise ValueError(f'supplement_idx({supplement_idx}) > reason_idx=({reason_idx})')
    bill_text = BillText(None)
    bill_text.id = bill_id
    bill_text.body = ''.join(texts[:supplement_idx])
    bill_text.supplement = ''.join(texts[supplement_idx + 1:reason_idx])
    bill_text.reason = ''.join(texts[reason_idx + 1:])
    return bill_text
