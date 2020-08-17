from crawler.spiders import SpiderTemplate


class MlitSpider(SpiderTemplate):
    name = 'mlit'  # 国土交通省
    domain = 'mlit.go.jp'
    start_urls = ['https://www.mlit.go.jp/policy/file000003.html#201']
