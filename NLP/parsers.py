from datetime import datetime, date, timedelta

import requests
from bs4 import BeautifulSoup
from unicodedata2 import normalize
import traceback

class BaseParser():

    USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0"

    def parse_news(self, count):
        raise NotImplementedError

class MeduzaParser(BaseParser):

    url = 'https://meduza.io/api/v3/search?chrono=news&locale=ru&page={page}&per_page=24'

    def parse_news(self, count=5000):
        news = []
        cur_page = 1

        while count > 0:
            try:
                page_news = self.get_page_data(page=cur_page)
                news.extend(page_news)
                count -= len(page_news)
                cur_page += 1
            except:
                traceback.print_exc()

        return news

    def get_page_data(self, page, site_url="https://meduza.io/{0}"):
        headers = {'User-agent' : self.USER_AGENT}
        response = requests.get(self.url.format(page=page), headers=headers).json()
        
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

                body = " ".join(text_content)
                
                date = page_content.find("time").text
                date = self.parse_date(date)
                
                author = page_content.find("time").parent.parent
                author = author.find_all("div", recursive=False)[1]
                try:
                    author = author.find("a").text
                except:
                    if "Meduza" in author.text:
                        author = "Meduza"
                    else:
                        author = author.text

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


class LentaParser(BaseParser):

    base_url = 'https://lenta.ru/'

    def parse_news(self, count=5000):
        news = []
        date_delta = 0

        while count > 0:
            cur_date = str(date.today() - timedelta(days=date_delta)).replace('-','/')
            try:
                page_news = self.get_page_data(date=cur_date)
                news.extend(page_news)
                count -= len(page_news)
                date_delta += 1
            except:
                traceback.print_exc()

        return news

    def get_page_data(self, date):
        headers = {'User-agent' : self.USER_AGENT}
        page_responce = requests.get(self.base_url + date)

        page_content = BeautifulSoup(page_responce.content, "html.parser")
        urls = ['https://lenta.ru' + i.a['href'] for i in page_content.find_all('div', {"class":"titles"})]

        result = []
        for url in urls:

            page_responce = requests.get(url, headers=headers)
            if page_responce.status_code == 200:
                page_content = BeautifulSoup(page_responce.content, "html.parser")

                try:
                    title = page_content.find_all("h1")[0].text
                except:
                    continue

                body = ' '.join([p.text for p in page_content.find_all('p')])

                try:
                    date = page_content.find("time", {"class": "g-date"})['datetime']
                    date = datetime.strptime(date[:-6], '%Y-%m-%dT%H:%M:%S')
                except:
                    date = None

                entry = {"author": None,
                         "title" : title,
                         "body" : body,
                         "date": date}
                result.append(entry)
                
        return result


class AifParser(BaseParser):

    base_url = "http://www.aif.ru/{rubric}"
    rubrics = {'society',
               'incidents',
               'politics',
               'money',
               'culture',
               'sport'}

    def parse_news(self, count=5000):
        news = []
        cur_page = 1

        while count > 0:
            for rubric in self.rubrics:
                try:
                    page_news = self.get_page_data(rubric=rubric,
                                                   page=cur_page)
                    news.extend(page_news)
                    count -= len(page_news)
                except:
                    pass
                print(f'\rcount: {count}', end="")
            cur_page += 1

        return news

    def get_page_data(self, rubric, page):
        headers = {'User-agent' : self.USER_AGENT}
        page_responce = requests.post(self.base_url.format(rubric=rubric),
                                      headers=headers,
                                      data={"page": page})

        page_content = BeautifulSoup(page_responce.content, "html.parser")
    
        urls = page_content.find_all("a", {"class": "rubric_img"})
        urls = [url['href'] for url in urls]

        result = []
        for url in urls:
            page_responce = requests.get(url, headers=headers, timeout=5)
            if page_responce.status_code == 200:
                page_content = BeautifulSoup(page_responce.content, "html.parser")

                title = page_content.h1.text

                body = page_content.article
                all_links = body.find_all("a")
                for link in all_links:
                    link.extract()
                all_scripts = body.find_all("script")
                for script in all_scripts:
                    script.extract()
                body = normalize('NFKD', page_content.article.text)

                date = page_content.find("time")['datetime']
                date = datetime.strptime(date, '%Y-%m-%dT%H:%M')

                author = page_content.find("a", {"class": "io-author_didgital"})
                if author is None:
                    author = "aif"
                else:
                    author = author.text

                entry = {"author": author,
                         "title" : title,
                         "body" : body,
                         "date": date,
                         "rubric": rubric}
                result.append(entry)

        return result