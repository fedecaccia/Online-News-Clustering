import settings
from threading import Thread
import feedparser
import requests
from requests import ConnectionError
from dragnet import extract_content, extract_comments
import time
from langdetect import detect # lento
from textblob import TextBlob
from datetime import datetime
import dataset
import urllib2

class FeedWorker(Thread):
    def __init__(self, feeds_queue, pages_queue, crawled_urls, mutex):
        Thread.__init__(self)
        self.feeds_queue = feeds_queue
        self.pages_queue = pages_queue
        self.crawled_urls = crawled_urls
        self.mutex = mutex

    def run(self):
        item = self.feeds_queue.get()

        while item != None:
            d = feedparser.parse(item)

            for post in d.entries:
                try:
                    post.link = self.filter_url(post.link)
                except:
                    pass
                else:
                    self.mutex.acquire()
                    if post.link not in self.crawled_urls and self.is_not_forbidden(post):
                        self.crawled_urls.add(post.link)
                        try:
                            created = post.published # news
                        except:
                            created = post.updated # reddit
                        self.pages_queue.put({'title':post.title, 'page':post.link, 'date':created})
                    self.mutex.release()

            time.sleep(0.1)
            self.feeds_queue.put(item)
            item = self.feeds_queue.get()

    def is_not_forbidden(self, post):
        
        # solo devuelve el contenido con extract_comments, pero con terminos y condiciones
        if "financemagnates" in post.link:
            return False
        if "ambcrypto" in post.link: # lee mal
            return False
        # # if "https://medium.com/@koinmedya" in link: # ruso?
        #     return False
        # if "https://medium.com/@clickchain/" in link:
        #     return False
        # if "https://medium.com/@rojisaeroji92" in link:
        #     return False
        # if "https://medium.com/@eosys" in link:
        #     return False
        # if "ft.com" in link: # requiere suscripcion, lee cualquier cosa
        #     return False
        if "reddit" in post.link:
            try:
                if post.updated is not None and settings.reddit==True:
                    return True
            except:
                pass
            return False
        if "twitter" in post.link:
            return False
        return True

    def filter_url(self, link):
        if "/#" in link: # unifico links que llegan con distinto #comment
            return link.split("/#")[0]
        if "?source" in link: # medium con diferente sources por feed
            return link.split("?source")[0]
        return link


class PageWorker(Thread):
    def __init__(self, pages_queue, crawled_urls, mutex, news_id, news_queue):
        Thread.__init__(self)
        self.pages_queue = pages_queue
        self.crawled_urls = crawled_urls
        self.mutex = mutex
        self.news_id = news_id
        self.news_queue = news_queue
        db = dataset.connect(settings.scraper_db)
        self.table = db[settings.news_table]

    def run(self):
        item = self.pages_queue.get()

        while item != None:
            try:
                r = requests.get(item['page'])
            except ConnectionError as e:
                # print(e)
                pass
            else:
                if r.status_code != 200:
                    # print(datetime.now(), self.name, "WARNING: Removing url with bad response:", r.status_code, item["page"])
                    if r.status_code != 403: # else it is forbidden
                        self.crawled_urls.remove(item["page"])
                else:
                    content = self.scraper(r.content, item["page"])
                    if self.content_is_important(content): # not empty
                    # if not not content.strip(): # not empty
                        if self.my_string_has_language(content, "en"):
                            self.mutex.acquire()
                            
                            # print(datetime.now(), self.news_id[0], item["page"])
                            self.news_id[0] += 1                       
                            self.news_queue.put({
                                "id_str":self.news_id[0],
                                "created_at":item["date"],
                                "user_name":item["page"].encode('utf-8'),
                                "content":content.encode('utf-8')
                            })
                            # file = "news/doc"+str(self.news_id[0])+".txt"
                            # doc_file = open(file, "w")
                            # doc_file.write(str(item["date"])+"\n")
                            # doc_file.write(item["page"].encode('utf-8')+"\n")
                            # doc_file.write(content.encode('utf-8'))
                            # doc_file.close()                            
                            self.table.insert(dict(
                                created_at=item["date"],
                                user_name=item["page"],
                                content=content
                            ))
                            self.mutex.release()
                        else:
                            # print(datetime.now(), self.name, "WARNING: unknown language", item["page"], content)
                            pass
                    else:
                        # print(datetime.now(), self.name, "WARNING: content empty or not important extracted from:", item["page"], content)
                        pass
            item = self.pages_queue.get()

        print(self.name, "finish")

    def content_is_important(self, content):
        if not content.strip():
            return False
        else:
            for word in settings.track_terms:
                if word in content:
                    return True
            return False

    def scraper(self, html, link):
        text = extract_content(html)
        if "cnbc" in link: # in this case content is extracted also in the comments
            text += " " + extract_comments(html)
        text = text.split("disclaimer")[0]
        return text

    def my_string_has_language(self, text, language): # lento!!!!
        # text = self.robust_decode(text)
        try:
            if detect(text) == language: # lento!!!!
            # if TextBlob(text).detect_language()==language:
                return True
        except urllib2.HTTPError as err:
            raise urllib2.HTTPError("Google Translation API connection is in trouble. Try commenting line 165 in workers.py and uncommenting line 164.")
        except:
            pass
        return False
        # return True

    def robust_decode(self, bs):
        '''Takes a byte string as param and convert it into a unicode one.
        First tries UTF8, and fallback to Latin1 if it fails'''
        cr = None
        try:
            cr = bs.encode('utf8')
        except UnicodeDecodeError:
            cr = bs.decode('latin1')
        except Exception as e:
            pass
        return cr