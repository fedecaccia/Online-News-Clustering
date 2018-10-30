import settings
import private
import tweepy
import dataset
from textblob import TextBlob
from sqlalchemy.exc import ProgrammingError
from Queue import Queue
import json
from abc import ABCMeta, abstractmethod

from workers import FeedWorker, PageWorker
from threading import Lock
from xml.etree import ElementTree

class Scraper(object):

	"""Scraper: Generic scrapper class"""

	__metaclass__ = ABCMeta

	def __init__(self):
		self.db = dataset.connect(settings.scraper_db)
		self.items_queue = Queue()

	@abstractmethod
	def listen(self):
		pass

	def get_item(self):
		item = self.items_queue.get()
		item["id"] = item["id_str"]
		return item

class NewsScraper(Scraper):

	"""NewsScraper: Scrape news from feeds"""

	def __init__(self):
		super(NewsScraper, self).__init__()
		self.feeds = self.extract_rss_urls_from_opml(settings.news_feed_file)

		self.feeds_queue = Queue()
		self.pages_queue = Queue()
		self.crawled_urls = set()
		self.news_id = [0]
		self.N_OF_FEED_WORKERS = 20
		self.N_OF_PAGE_WORKERS = 30

	def extract_rss_urls_from_opml(self, filename):
		urls = []
		with open(filename, 'rt') as f:
			tree = ElementTree.parse(f)
		for node in tree.findall('.//outline'):
			url = node.attrib.get('xmlUrl')
			if url:
				urls.append(url)
		return urls

	def listen(self):
		for feed in self.feeds:
			self.feeds_queue.put(feed)
		self.run_feed_workers()

	def run_feed_workers(self):
		feed_workers = []
		page_workers = []
		mutex = Lock()
		for i in range(self.N_OF_FEED_WORKERS):
			worker = FeedWorker(self.feeds_queue, self.pages_queue, self.crawled_urls, mutex)
			feed_workers.append(worker)
			worker.start()

		for i in range(self.N_OF_PAGE_WORKERS):
			worker = PageWorker(self.pages_queue, self.crawled_urls, mutex, self.news_id, self.items_queue)
			page_workers.append(worker)
			worker.start()


class TwitterScraper(Scraper):

	"""TwitterScraper: Asyncronich twitter scraper class"""

	def __init__(self):
		super(TwitterScraper, self).__init__()
		auth = tweepy.OAuthHandler(private.TWITTER_APP_KEY, private.TWITTER_APP_SECRET)
		auth.set_access_token(private.TWITTER_KEY, private.TWITTER_SECRET)
		self.api = tweepy.API(auth)
		self.stream_listener = StreamListener(self.db, self.items_queue) 

	# This function is separated from constructor, because twitter stream can be diconnected,
	# and so recconected using this
	def listen(self):

		stream = tweepy.Stream(auth=self.api.auth, listener=self.stream_listener)
		stream.filter(track=settings.track_terms, async=True)

class StreamListener(tweepy.StreamListener):

	"""Listen data from twitter"""

	def __init__(self, db, items_queue):
		super(StreamListener, self).__init__()
		self.db = db
		self.items_queue = items_queue        

	def on_status(self, status):
		# if status.retweeted:
		#     return

		# https://developer.twitter.com/en/docs/tweets/data-dictionary/overview/tweet-object

		description = status.user.description
		loc = status.user.location
		text = status.text
		coords = status.coordinates # [lat, long]
		name = status.user.screen_name
		user_created = status.user.created_at
		followers = status.user.followers_count
		id_str = status.id_str
		created = status.created_at
		retweets = status.retweet_count
		favorite_count = status.favorite_count
		bg_color = status.user.profile_background_color
		blob = TextBlob(text)
		sent = blob.sentiment

		if settings.download_retweets==True or (settings.download_retweets==False and text[:2]!="RT"):

			if coords is not None:
				coords = json.dumps(coords)

			table = self.db[settings.tweets_table]

			data = dict(
					user_description=description,
					user_location=loc,
					coordinates=coords,
					content=text,
					user_name=name,
					user_created_at=user_created,
					user_followers=followers,
					id_str=id_str,
					created_at=created,
					retweet_count=retweets,
					favorite_count=favorite_count,
					user_bg_color=bg_color,
					polarity=sent.polarity,
					subjectivity=sent.subjectivity
				)

			try:
				table.insert(data)
			except ProgrammingError as err:
				print(err)            
			try:
				self.items_queue.put(data)
			except ProgrammingError as err:
				print(err)

	def on_error(self, status_code):
		if status_code == 420:
			#returning False in on_data disconnects the stream
			return False