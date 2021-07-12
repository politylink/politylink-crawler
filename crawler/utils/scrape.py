import json
import re
from datetime import datetime
from urllib.parse import urljoin

from politylink.graphql.schema import ParliamentaryGroup


def extract_text(cell):
    return cell.xpath('.//text()').get()


def extract_full_href_or_none(cell, root_url):
    selector = cell.xpath('.//a/@href')
    if len(selector) > 0:
        return urljoin(root_url, selector.get())
    return None


def extract_full_href_list(selector, root_url):
    urls = []
    for element in selector:
        maybe_url = extract_full_href_or_none(element, root_url)
        if maybe_url:
            urls.append(maybe_url)
    return urls


def extract_json_ld_or_none(response):
    maybe_text = response.xpath('//script[@type="application/ld+json"]//text()').get()
    if not maybe_text:
        return None
    return json.loads(maybe_text)


def extract_thumbnail_or_none(ld_json):
    if 'image' not in ld_json or 'url' not in ld_json['image']:
        return None
    return ld_json['image']['url']


def extract_datetime(dt_str):
    pattern = r'(\d+)年(\d+)月(\d+)日'
    m = re.search(pattern, dt_str)
    if not m:
        raise ValueError(f'{dt_str} does not match with {pattern}')
    return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def extract_parliamentary_group_or_none(s: str):
    """
    https://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/shiryo/kaiha_m.htm
    https://www.sangiin.go.jp/japanese/joho1/kousei/giin/kaiha/kaiha204.htm
    """

    groups_names = {
        ParliamentaryGroup.JIMIN: {'自民', '自由民主党・無所属の会', '自由民主党・国民の声'},
        ParliamentaryGroup.RIKKEN: {'立民', '立憲民主党・無所属', '立憲', '立憲民主・社民'},
        ParliamentaryGroup.KOMEI: {'公明', '公明党'},
        ParliamentaryGroup.KYOSAN: {'共産', '日本共産党'},
        ParliamentaryGroup.ISHIN: {'維新', '日本維新の会・無所属の会', '日本維新の会'},
        ParliamentaryGroup.KOKUMIN: {'国民', '国民民主党・無所属クラブ', '民主', '国民民主党・新緑風会'}
    }

    for group, names in groups_names.items():
        if s in names:
            return group
    return None


def extract_parliamentary_groups(s: str, separator=';'):
    groups = []
    for ss in s.split(separator):
        maybe_group = extract_parliamentary_group_or_none(ss.strip())
        if maybe_group:
            groups.append(maybe_group)
    return groups
