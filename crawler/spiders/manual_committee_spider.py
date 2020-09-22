from logging import getLogger

from crawler.spiders import SpiderTemplate
from crawler.utils import build_committee

LOGGER = getLogger(__name__)

# copied from http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/kokkai/kokkai_gensoku.htm
main_desc = '本会議は、その議院の議員全員の会議であり、議院の最終的な意思はここで決定されます。' \
            '本会議は、公開が原則であり、本会議を開くには総議員の３分の１以上の出席が必要です。' \
            'その議事は特別の場合を除き、出席議員の過半数の賛成で決められます。' \
            'また、本会議は、通常、衆議院では火曜・木曜・金曜日の午後１時、参議院では月曜・水曜・金曜日の午前１０時から開かれます。'

# copied from http://www.shugiin.go.jp/internet/itdb_kenpou.nsf/html/kenpou/index.htm
kenpou_desc = '憲法審査会は、日本国憲法及び日本国憲法に密接に関連する基本法制について広範かつ総合的に調査を行い、' \
              '憲法改正原案、日本国憲法に係る改正の発議又は国民投票に関する法律案等を審査する機関です。 ' \
              '本審査会は、第167回国会の召集の日（平成19年8月7日）から、国会法第102条の6の規定に基づき「（衆議院に）設ける」とされています。'

# copied from http://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/shiryo/jyouhoukanshi.htm
jouhou_desc = '情報監視審査会は、行政における特定秘密の保護に関する制度の運用を常時監視するため特定秘密の指定・解除及び適性評価の実施状況について調査を行うとともに、' \
              '委員会等が行った特定秘密の提出要求に行政機関の長が応じなかった場合に、その判断の適否等について審査を行う機関です。' \
              '本審査会は、国会法第102条の13の規定に基づき平成26年12月から設置されています。'

seiji_desc = '政治倫理審査会は、政治倫理の確立のため、議員が「行為規範」その他の法令の規定に著しく違反し、' \
             '政治的道義的に責任があると認めるかどうかについて審査し、適当な勧告を行う機関です。' \
             '本審査会は、国会法に基づき、第１０４回国会の昭和６０年１２月から設置されています。'


class ManualCommitteeSpider(SpiderTemplate):
    name = 'manual_committee'
    start_urls = ['https://google.com']

    def parse(self, response):
        committees = [
            build_committee('衆議院本会議', 'REPRESENTATIVES', 465, description=main_desc),
            build_committee('参議院本会議', 'COUNCILORS', 248, description=main_desc),
            build_committee('衆議院憲法審査会', 'REPRESENTATIVES', None, description=kenpou_desc),
            build_committee('衆議院情報監視審査会', 'REPRESENTATIVES', None, description=jouhou_desc),
            build_committee('衆議院政治倫理審査会', 'REPRESENTATIVES', None, description=seiji_desc),
        ]
        for committee in committees:
            self.client.exec_merge_committee(committee)
        LOGGER.info(f'merged {len(committees)} committees')
