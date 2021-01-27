from crawler.spiders import DietTableSpiderTemplate


class ShuhouSpider(DietTableSpiderTemplate):
    name = 'shuhou'  # 衆議院法制局
    domain = 'shugiin.go.jp'
    bill_category = 'SHUHOU'

    table_idx = 0
    bill_col = 1
    url_col = 5

    @staticmethod
    def build_start_url(diet_number):
        return f'http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/housei/html/h-shuhou{diet_number}.html'
