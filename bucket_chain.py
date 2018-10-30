import time
import settings
from bucket import Bucket
import numpy as np
import spacy
from string import punctuation
from sklearn.feature_extraction import text
from sklearn.feature_extraction.text import CountVectorizer

class BucketChain(object):

	"""BucketChain: Chain of buckets of items: previous and posterior buckets to the analyzed bucket serve to perform term symilar analyis"""

	def __init__(self, debug, chrono, universe, source):
		self.debug = debug
		self.chrono = chrono
		self.universe = universe        
		self.source = source
		self.buckets = []
		self.n_buckets = 0     
		self.n_look_ahead = settings.n_look_ahead_buckets
		self.max_buckets = settings.bucket_history
		self.analyzed_bucket = None
		self.analyzed_pos = self.max_buckets-1-self.n_look_ahead
		new_stop_words=list(settings.extra_stop_words)
		my_stop_words = text.ENGLISH_STOP_WORDS.union(np.concatenate([new_stop_words,list(punctuation)]))
		self.vectorizer = CountVectorizer(stop_words=my_stop_words)
		self.stemming = spacy.load(settings.language, disable = ['tagger', 'parser', 'ner'])

	def is_updated(self):
		self.debug.log("Initializing new bucket...")
		self.add_bucket()
		self.check_chain_size()
		self.analyzed_bucket = self.get_analyzed_bucket()
		if self.analyzed_bucket:
			self.debug.log("Bucket chain is ready to cluster")
			return True
		return False

	def add_bucket(self):
		operation_time = time.time()
		self.buckets.append(Bucket(bucket_id=self.n_buckets, 
			debug=self.debug, chrono=self.chrono, universe=self.universe, source=self.source,
			vectorizer=self.vectorizer, stemming=self.stemming))
		self.n_buckets += 1
		self.debug.log("\tFinished in: "+str(time.time()-operation_time))

	def check_chain_size(self):
		if self.n_buckets > self.max_buckets:
			self.remove_old_bucket()

	def remove_old_bucket(self):
		for item in self.buckets[0].items:
			cluster = item.in_cluster
			# first buckets could be discarded because they are just used in pre-clustering work
			if cluster is not None:
				cluster.decrease_items_in_buckets()
		self.buckets.pop(0)
		self.n_buckets -= 1

	def get_analyzed_bucket(self):
		if self.n_buckets == self.max_buckets:            
			return self.buckets[self.analyzed_pos]
		else:
			return None

	def compute_universal_counts(self):
		self.debug.log("Computing bucket universal counts")
		operation_time = time.time()
		for bucket in self.buckets:
			for item in bucket.items:
				item.compute_universal_counts()
		self.debug.log("\tFinished in: "+str(time.time()-operation_time))

	def compute_universal_tfidf(self):
		self.debug.log("Computing bucket universal tfidf")
		operation_time = time.time()
		for bucket in self.buckets:
			for item in bucket.items:
				item.compute_universal_tfidf()
		self.debug.log("\tFinished in: "+str(time.time()-operation_time))

	def assign_default_vector_expansion(self):
		for item in self.analyzed_bucket.items:
			item.set_tfidf_expanded(item.tfidf)
