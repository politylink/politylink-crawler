from crawler.spiders import SpiderTemplate


class EnvSpider(SpiderTemplate):
    name = 'env'  # 環境省
    domain = 'env.go.jp'
    start_urls = ['http://www.env.go.jp/info/hoan/index.html']
