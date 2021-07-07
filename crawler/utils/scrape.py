import json
import re
from datetime import datetime
from urllib.parse import urljoin


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
