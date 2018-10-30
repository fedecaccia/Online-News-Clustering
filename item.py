import settings

class Item(object):

	"""Item: An item to be clusterized"""

	def __init__(self, item_id, features, debug, universe, vectorizer, stemming):
		self.id = item_id
		self.in_cluster = None

		self.user = features["user_name"]
		if settings.source=="twitter":
			self.user_followers = features["user_followers"]
			self.user_created_at = features["user_created_at"]

		self.created_at = features["created_at"]
		self.content = features["content"]
		self.debug = debug
		self.universe = universe
		self.local_terms = None
		self.local_counts = None
		self.universal_counts = None
		self.tfidf = None
		self.tfidf_expanded = None
		self.vectorizer = vectorizer
		self.stemming = stemming		
		self.tokenize_and_remove_stop_words()
		self.compute_stemming()

	def tokenize_and_remove_stop_words(self):
		self.local_counts = self.vectorizer.fit_transform([self.content]).toarray()[0]
		self.local_terms = self.vectorizer.get_feature_names()

	def compute_stemming(self):
		for i_term, term in enumerate(self.local_terms,0):
			stem = self.stemming(term)
			self.local_terms[i_term] = stem[0].lemma_

	def compute_universal_counts(self):
		self.universal_counts = self.universe.get_universal_item_counts(self.local_terms, self.local_counts)
		# self.debug.log("\titem universal counts shape:"+str(self.universal_counts.shape))
		# self.debug.log("\tuniversal df shape:"+str(self.universe.df.shape))

	def compute_universal_tfidf(self):
		self.tfidf = self.universe.get_universal_tfidf(self.universal_counts)
		# self.debug.log("\titem universal tfidf shape:"+str(self.universal_tfidf.shape))

	def set_cluster(self, cluster):
		self.in_cluster = cluster

	def set_tfidf_expanded(self, tfidf_expanded):
		self.tfidf_expanded = tfidf_expanded