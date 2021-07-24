"""
Elasticsearchインスタンスを生成するためのbuildメソッドを定義する

ここでは長いテキストデータのみを保存する
その他のフィールドはelasticsearch_syncerで定期的に同期し直す
"""

from politylink.elasticsearch.schema import BillText, MemberText
from politylink.graphql.schema import Member


def build_bill_text(bill_id, texts):
    supplement_idx = texts.index('附 則')
    reason_idx = texts.index('理 由')
    if supplement_idx > reason_idx:
        raise ValueError(f'supplement_idx({supplement_idx}) > reason_idx=({reason_idx})')
    body = ''.join(texts[:supplement_idx])
    supplement = ''.join(texts[supplement_idx + 1:reason_idx])
    reason = ''.join(texts[reason_idx + 1:])

    bill_text = BillText()
    bill_text.set(BillText.Field.ID, bill_id)
    bill_text.set(BillText.Field.BODY, body)
    bill_text.set(BillText.Field.SUPPLEMENT, supplement)
    bill_text.set(BillText.Field.REASON, reason)
    return bill_text


def build_member_text(member: Member):
    member_text = MemberText()
    member_text.set(MemberText.Field.ID, member.id)
    member_text.set(MemberText.Field.DESCRIPTION, member.description)
    return member_text
