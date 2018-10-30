import settings
import time
from tsa import TSA

class OnlineClustering(object):

	"""OnlineClustering: Algorithms to perform online clustering over items"""

	def __init__(self, debug, universe, bucket_chain, clusters):
		self.debug = debug
		self.universe = universe
		self.bucket_chain = bucket_chain
		self.clusters = clusters
		self.tsa = TSA(debug, universe, bucket_chain, clusters)

	def pre_clustering_work(self):
		if settings.tsa == True:
			self.debug.log("Pre-clustering work...")
			operation_time = time.time()
			self.tsa.compute()
			self.debug.log("\tFinished in: "+str(time.time()-operation_time))

	def online_clustering(self):
		self.debug.log("Clustering...")
		operation_time = time.time()
		for item in self.bucket_chain.analyzed_bucket.items:			
			max_sim_val, max_sim_cluster = self.clusters.get_max_similarity(item)
			if max_sim_val > settings.merge_threshold:
				self.clusters.merge_item(max_sim_cluster, item)				
			else:
				self.clusters.create_cluster(item)
		self.debug.log("\tFinished in: "+str(time.time()-operation_time))
		if self.clusters.centroid_counts is not None:
			self.debug.log("\tCentroids shape: "+str(self.clusters.centroid_counts.shape))