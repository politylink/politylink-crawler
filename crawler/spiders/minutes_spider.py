from logging import getLogger

import json
import scrapy


LOGGER = getLogger(__name__)


START_DAY = "2020-05-01"
END_DAY = "2020-07-10"
MAX_NUM = 5  # 仕様書には、会議単位出力の場合は「1～30」の範囲で指定可能と書いてあるが、5より大きいとエラーが出る
OUTPUT_FORMAT = "json"


class MinutesSpider(scrapy.Spider):
    name = 'minutes'
    domain = 'kokkai.ndl.go.jp'
    end_point = "https://kokkai.ndl.go.jp/api/meeting?from={0}&until={1}&startRecord={2}&maximumRecords={3}&recordPacking={4}"
    next_pos = 1
    meeting_lst = []

    def __init__(self, *args, **kwargs):
        super(MinutesSpider, self).__init__(*args, **kwargs)
        # self.client = GraphQLClient()

    def start_requests(self):
        while self.next_pos is not None:
            url = self.end_point.format(START_DAY, END_DAY, self.next_pos, MAX_NUM, OUTPUT_FORMAT)
            yield scrapy.Request(url, self.parse)

        self.format_minutes(self.meeting_lst)

    def parse(self, response):
        response = json.loads(response.body)
        # add meeting information of current request
        self.meeting_lst.extend(response["meetingRecord"])
        # get next start position of record
        self.next_pos = response["nextRecordPosition"]

    @staticmethod
    def format_minutes(meeting_lst):
        format_meeting_dctlst = {
            "issueID": [], "date": [], "imageKind": [], "issue": [], "nameOfHouse": [],
            "nameOfMeeting": [], "session": [], "pdfURL": []}
        format_speech_dctlst = {
            "issueID": [], "speechOrder": [], "speaker": [], "speakerYomi": [],
            "speakerGroup": [], "speakerPosition": [], "speakerRole": [],
            "speechID": [], "speech": [], "speechURL": []}

        # get each value
        for i in range(len(meeting_lst)):
            meeting = meeting_lst[i]

            # update format meeting table
            for key in format_meeting_dctlst.keys():
                format_meeting_dctlst[key].append(meeting[key])

            speeches = meeting["speechRecord"]
            for speech in speeches:
                speech["issueID"] = meeting["issueID"]
                # update format speech table
                for key in format_speech_dctlst.keys():
                    format_speech_dctlst[key].append(speech[key])

        print(len(format_speech_dctlst.keys()))
        print(len(format_speech_dctlst["speechID"]))

