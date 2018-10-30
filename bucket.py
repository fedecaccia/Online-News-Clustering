import settings
import time
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse import csr_matrix
from item import Item

class Bucket(object):

	"""Bucket: Group of items to be preprocessed and then clustered"""

	def __init__(self, bucket_id, debug, chrono, universe, source, vectorizer, stemming):
		self.id = bucket_id
		self.debug = debug
		self.source = source
		self.chrono = chrono
		self.universe = universe
		self.vectorizer = vectorizer
		self.stemming = stemming
		self.items = []
		self.n_items = 0
		self.last_item = None
		self.min_items = settings.min_items_per_bucket
		self.min_time_listening = settings.min_time_per_bucket
		self.starting_time = self.chrono.get_utc_time()
		self.term_item_matrix = None
		self.listen()

	def listen(self):
		while self.is_time_to_listen():
			posible_item = self.source.get_item()
			if self.item_is_valid(posible_item):
				self.add_item(posible_item)

	def is_time_to_listen(self):
		time_listening = (self.chrono.get_utc_time() - self.starting_time).total_seconds()
		listening_condition1 =  time_listening < self.min_time_listening
		listening_condition2 = self.n_items<self.min_items
		if listening_condition1 or listening_condition2:
			return True
		return False

	def item_is_valid(self, item):
		cond1 = self.check_item_creation_time(item)
		cond2 = self.check_item_creator_created_time(item)
		cond3 = self.check_item_creator_followers(item)
		cond4 = self.check_item_retweeted(item)
		cond5 = self.check_tweet_creator(item)
		if cond1 and cond2 and cond3 and cond4 and cond5:
			return True
		return False

	def check_item_creation_time(self, item):
		item["created_at"] = pd.to_datetime(item["created_at"])
		time_difference = abs(item["created_at"] - self.chrono.get_utc_time()).total_seconds()
		if time_difference < settings.historic_window:
			return True
		return False

	def check_item_creator_created_time(self, item):
		if settings.source == "twitter":
			user_created = pd.to_datetime(item["user_created_at"])
		else:
			return True
		time_difference = abs(user_created - self.chrono.get_utc_time()).total_seconds()
		if time_difference > settings.min_user_life:
			return True
		return False

	def check_item_creator_followers(self, item):
		if settings.source == "twitter":
			followers = item["user_followers"]
		else:
			return True			
		if followers > settings.min_user_followers:
			return True
		return False

	def check_item_retweeted(self, item):
		if settings.source == "twitter" and item["content"][:2]=="RT":
			return False
		return True

	def check_tweet_creator(self, item):
		if settings.source == "twitter" and settings.check_tweet_user_creator:
			if item["user_name"] in settings.valid_twitter_users:
				return True
			return False
		return True

	def add_item(self, posible_item):
		self.items.append(Item(item_id=self.n_items, features=posible_item,
								debug=self.debug, universe=self.universe,
								vectorizer=self.vectorizer, stemming=self.stemming))
		self.n_items += 1
		self.universe.increase_items()
		self.last_item = self.items[-1]
		if self.last_item.created_at > self.chrono.last_update:
			self.chrono.set_last_update(self.last_item.created_at)
		self.universe.update_terms(self.last_item.local_terms)		