from logging import getLogger
from urllib.parse import urljoin

from crawler.spiders import SpiderTemplate
from crawler.utils.common import parse_name_str
from crawler.utils.elasticsearch import build_member_text
from crawler.utils.graphql import build_member, build_url, UrlTitle
from crawler.utils.scrape import extract_text, extract_full_href_or_none, extract_parliamentary_group_or_none
from politylink.graphql.schema import Member

LOGGER = getLogger(__name__)


class ShugiinMemberSpider(SpiderTemplate):
    name = 'shugiin_member'
    domain = 'shugiin.go.jp'

    def __init__(self, text='false', *args, **kwargs):
        super(ShugiinMemberSpider, self).__init__(*args, **kwargs)
        self.collect_text = text == 'true'
        self.start_urls = [f'http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/syu/{i}giin.htm'
                           for i in range(1, 11)]

    def parse(self, response):
        members, urls = self.scrape_members_and_urls(response)
        self.gql_client.bulk_merge(members)
        LOGGER.info(f'merged {len(members)} members')

        for url in urls:
            member_id = url.meta['member_id']
            self.delete_old_urls(member_id, url.title)
            self.gql_client.merge(url)
            self.gql_client.link(url.id, member_id)
            yield response.follow(url.url, callback=self.parse_member, meta=url.meta)

    def parse_member(self, response):
        member = Member(None)
        member.id = response.meta['member_id']
        contents = response.xpath('//div[@id="contents"]')

        name_str = contents.xpath('./h2/text()').get()
        try:
            member.first_name, member.last_name, member.first_name_hira, member.last_name_hira = \
                parse_name_str(name_str)
            member.name_hira = member.last_name_hira + member.first_name_hira
        except ValueError as e:
            LOGGER.warning(f'failed to parse name={name_str}: e={e}')

        desc = []
        for text in contents.xpath('.//text()').getall():
            text = text.strip()
            if text:
                desc.append(text)
        member.description = ' '.join(desc)

        maybe_image_src = response.xpath('//div[@id="photo"]/img/@src').get()
        if maybe_image_src:
            member.image = urljoin(response.url, maybe_image_src)

        self.gql_client.merge(member)
        LOGGER.info(f'merged details for {member.id}')

        if self.collect_text:
            member_text = build_member_text(member)
            self.es_client.index(member_text)
            LOGGER.info(f'merged MemberText in Elasticsearch for {member.id}')

    def scrape_members_and_urls(self, response):
        members, urls = [], []
        table = response.xpath('//table[@width="100%"]')[0]
        for row in table.xpath('./tr')[1:]:  # skip header
            cells = row.xpath('./td')
            assert len(cells) == 5

            name = ''.join(extract_text(cells[0]).strip()[:-1].split())  # remove
            tags = [  # store 会派 and 選挙区 as tags for now
                extract_text(cells[2]).strip(),
                extract_text(cells[3]).strip()
            ]
            maybe_group = extract_parliamentary_group_or_none(tags[0])
            member = build_member(name)
            member.tags = tags
            member.house = 'REPRESENTATIVES'
            if maybe_group:
                member.group = maybe_group
            members.append(member)

            maybe_href = extract_full_href_or_none(cells[0], response.url)
            if maybe_href:
                url = build_url(maybe_href, UrlTitle.GIIN_ZYOUHOU, self.domain)
                url.meta = {'member_id': member.id}
                urls.append(url)
        return members, urls
