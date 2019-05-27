from datetime import datetime

import requests
from bs4 import BeautifulSoup
from unicodedata2 import normalize

class BaseParser():

    def parse_news(self, count):
        raise NotImplementedError

class MeduzaParser(BaseParser):

    STREAM = 'https://meduza.io/api/v3/search?chrono=news&page={page}&per_page=30&locale=ru'
    USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0"

    def parse_news(self, count=5000):
        news = []
        cur_page = 1

        while count > 0:
            page_news = self.get_page_data(page=cur_page,
                                           stream=self.STREAM,
                                           user_agent=self.USER_AGENT)
            news.extend(page_news)
            count -= len(page_news)

        return news

    def get_page_data(self, page, stream, user_agent, site_url="https://meduza.io/{0}"):
        headers = {'User-agent' : user_agent}
        response = requests.get(stream.format(page=page), headers=headers).json()
        
        result = []
        urls = [site_url.format(key) for key in response['documents'].keys()]
        for url in urls:
            if "news" not in url:
                continue

            page_responce = requests.get(url, headers=headers, timeout=5)

            if page_responce.status_code == 200:
                page_content = BeautifulSoup(page_responce.content, "html.parser")
                text_content = []
                title = normalize('NFKD', page_content.find_all("h1")[0].text)
                for i in range(0, len(page_content.find_all("p"))):
                    paragraphs = page_content.find_all("p")[i].text
                    text_content.append(normalize('NFKD', paragraphs))

                body = "".join(text_content)
                
                date = page_content.find("time").text
                date = self.parse_date(date)
                
                author = page_content.find("time").parent.parent
                author = author.find_all("div", recursive=False)[1]
                author = author.find("a").text

                entry = {"author": author,
                         "title" : title,
                         "body" : body,
                         "date": date}
                result.append(entry)
                
        return result

    def parse_date(self, str_date):
        months = {'января': '01',
                  'февраля': '02',
                  'марта': '03',
                  'апреля': '04',
                  'мая': '05',
                  'июня': '06',
                  'июля': '07',
                  'августа': '08',
                  'сентября': '09',
                  'октября': '10',
                  'ноября': '11',
                  'декабря': '12'}
        for old, new in months.items():
            if old in str_date:
                str_date = str_date.replace(old, new)
        date = datetime.strptime(str_date, '%H:%M, %d %m %Y')

        return date