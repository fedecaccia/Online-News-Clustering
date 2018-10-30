import settings
import time
import numpy as np
import pandas as pd
from scipy import sparse
import dataset
# import pystas

class Cluster(object):

	"""Cluster: a group of items that are similar each other in some metric"""

	def __init__(self, cluster_id, first_item, chrono, universe):
		self.chrono = chrono
		self.universe = universe
		self.id = cluster_id
		self.items = []
		self.n_items = 0
		self.items_yet_in_historical_buckets = 0
		self.created_at = first_item.created_at
		self.last_activity = first_item.created_at
		self.local_df_terms = dict()
		self.add_item(first_item)
		self.first_merging = True

	def add_item(self, item):
		self.items.append(item)
		item.set_cluster(self)
		self.n_items += 1
		self.items_yet_in_historical_buckets += 1
		self.update_last_activity(item.created_at)
		self.update_local_df_terms(item)

	def update_local_df_terms(self, item):
		for term in item.local_terms:
			if term in self.local_df_terms:
				self.local_df_terms[term] += 1
			else:
				self.local_df_terms[term] = 1

	def decrease_items_in_buckets(self):
		self.items_yet_in_historical_buckets -= 1
	
	def update_last_activity(self, date):
		if date > self.last_activity:
			self.last_activity = date

	def is_not_active(self):
		if (self.chrono.get_utc_time() - self.last_activity).total_seconds() < settings.cluster_max_inactive_life:
			return False
		if self.items_yet_in_historical_buckets>0:
			return False
		return True

	def get_local_df(self):
		local_df_like_universal_count = self.universe.get_universal_item_counts(self.local_df_terms.keys(), self.local_df_terms.values())
		return local_df_like_universal_count.T.toarray()[0]	


class Clusters(object):

	"""Clusters: A group of group of items that are similar each other in some metric"""

	def __init__(self, debug, chrono, universe):
		self.debug = debug
		self.chrono = chrono
		self.universe = universe
		self.clusters = np.array([])
		self.n_clusters = 0
		self.centroid_counts = None
		self.centroid_tfidf = None
		db = dataset.connect(settings.clusters_db)
		self.table = db[settings.store_clusters_table]

	def get_max_similarity(self, item):
		max_sim_val = 0
		max_sim_cluster = None
		if self.centroid_tfidf is not None:
			if settings.tsa:
				sim = self.centroid_tfidf.T.dot(item.tfidf_expanded).toarray()
			else:
				sim = self.centroid_tfidf.T.dot(item.tfidf).toarray()
			max_sim_val = np.max(sim)
			if max_sim_val > settings.merge_threshold:
				max_sim_cluster = self.clusters[np.where(sim==max_sim_val)[0][0]]
		return max_sim_val, max_sim_cluster

	def create_cluster(self, item):
		if settings.source != "twitter" or settings.source == "twitter" and item.user_followers>settings.new_clusters_min_followers:
			self.clusters = np.concatenate([self.clusters, np.array([Cluster(self.n_clusters, 
																				item, 
																				self.chrono,
																				self.universe)])])
			self.n_clusters += 1
			self.centroid_counts = sparse.hstack((self.centroid_counts, item.universal_counts))
			# efficient column indexing to merge
			self.centroid_counts = sparse.csc_matrix(self.centroid_counts)
			self.centroid_tfidf = sparse.hstack((self.centroid_tfidf, item.tfidf))
			self.centroid_tfidf = self.centroid_tfidf.tocsc()

	#@pystas.logpista
	def merge_item(self, cluster, item):
		cluster.add_item(item)
		cluster_position = np.where(self.clusters==cluster)[0][0]
		# change values in csr_matrix is expensive because add elements to .indices and .data
		# but converting this into lil takes more time
		self.centroid_counts[:, cluster_position] += item.universal_counts
		self.first_merging = False

	def update_centroid_counts(self):
		# add dummy rows due to new terms (added in new buckets)
		if self.centroid_counts is not None:
			self.debug.log("Updating centroid counts...")
			operation_time = time.time()
			self.centroid_counts = sparse.csc_matrix((self.centroid_counts.data,
														self.centroid_counts.indices,
														self.centroid_counts.indptr),
														shape=(self.universe.n_terms,
																self.n_clusters))
			self.debug.log("\tFinished in: "+str(time.time()-operation_time))
			self.debug.log("\tCentroids shape: "+str(self.centroid_counts.shape))

	def update_centroid_tfidf(self):
		if self.centroid_counts is not None and self.centroid_counts.shape[1]>0:
			self.debug.log("Updating centroid tfidf...")
			operation_time = time.time()
			self.centroid_tfidf = self.universe.get_universal_tfidf(self.centroid_counts)
			self.centroid_tfidf = self.centroid_tfidf.tocsc()
			self.debug.log("\tFinished in: "+str(time.time()-operation_time))
			self.debug.log("\tCentroids shape: "+str(self.centroid_tfidf.shape))
		else:
			self.centroid_tfidf = None

	def remove_old_clusters(self):
		self.debug.log("Checking for clusters to remove...")
		operation_time = time.time()
		clusters_to_delete = []
		removing_df = np.zeros(self.universe.n_terms)

		for i_cluster, cluster in enumerate(self.clusters):
			if cluster.is_not_active():				
				self.universe.remove_n_items(cluster.n_items)
				removing_df += cluster.get_local_df()
				clusters_to_delete.append(i_cluster)
				# self.store(cluster)
		if len(clusters_to_delete) > 0:				
			self.debug.log("\tRemoving "+str(len(clusters_to_delete))+" clusters")
			self.debug.log("\tInitial centroid counts shape: "+str(self.centroid_counts.shape))
			self.centroid_counts = self.centroid_counts[:, 
				[x for x in range(self.n_clusters) if x not in clusters_to_delete]]
			self.debug.log("\tFinal centroid counts shape: "+str(self.centroid_counts.shape))
			self.clusters = np.delete(self.clusters, clusters_to_delete)
			self.universe.remove_df(removing_df)
			self.n_clusters -= len(clusters_to_delete)
		self.debug.log("\tFinished in: "+str(time.time()-operation_time))

	def remove_terms(self, terms_to_remove_positions):
		if self.centroid_counts is not None:
			self.debug.log("\tRemoving "+str(len(terms_to_remove_positions))+" row terms from centroid counts positions..")
			self.debug.log("\tInitial shape:"+str(self.centroid_counts.shape))
			self.centroid_counts = self.delete_rows_csr(self.centroid_counts, terms_to_remove_positions)
			self.debug.log("\tFinal shape:"+str(self.centroid_counts.shape))

	def delete_rows_csr(self, mat, indices):
		"""
		Remove the rows denoted by ``indices`` form the CSR sparse matrix ``mat``.
		"""
		mat = mat.tocsr()
		if not isinstance(mat, sparse.csr_matrix):
			raise ValueError("works only for CSR format -- use .tocsr() first")
		indices = list(indices)
		mask = np.ones(mat.shape[0], dtype=bool)
		mask[indices] = False
		return mat[mask].tocsc()

	# DO NOT change cluster positions inplace, centroids preserve order
	# to later fnd terms and show
	def get_sorted_clusters_by_items(self):
		ordered_clusters = list(self.clusters)
		ordered_clusters.sort(key=lambda x: x.n_items, reverse=True)
		ordered_clusters = np.array(ordered_clusters)
		return ordered_clusters

	def debug_active_clusters(self):
		ordered_clusters = self.get_sorted_clusters_by_items()
		self.debug.log("")
		self.debug.log("Total clusters: "+str(self.n_clusters))
		for cluster in ordered_clusters[:settings.max_active_clusters_to_debug]:
			if cluster.n_items>settings.min_items_to_show_cluster:
				self.debug.log("")
				self.debug.log("\tCluster: "+str(cluster.id))
				self.debug.log("\tItems: "+str(cluster.n_items))				
				self.debug.log("\tTerms: "+self.get_relevant_terms(cluster))
				self.debug.log("\tCreated at: "+str(cluster.created_at))
				self.debug.log("\tLast activity: "+str(cluster.last_activity))
				if settings.show_items:
					for item in cluster.items:
						self.debug.log("\t\tItem id: "+str(item.id))
						self.debug.log("\t\tUser: "+str(item.user))
						self.debug.log("\t\tCreated at: "+str(item.created_at))
						self.debug.log("\t\tCreated at: "+str(item.created_at))
						self.debug.log(item.content)
		self.debug.log("")		

	def get_relevant_terms(self, cluster):
		cluster_position = np.where(self.clusters==cluster)[0][0]
		tfidf = self.centroid_tfidf[:,cluster_position].toarray().T[0]
		important_positions = [x for x in np.argsort(tfidf)[::-1] if tfidf[x]>0.1]
		msg = ""
		for important_position in important_positions:			
			for term, universal_position in self.universe.terms_positions.iteritems():
				if universal_position == important_position:
					msg += term+" "
		return msg
	
	def save_active_clusters(self):
		
		self.debug.log("Writing active clusters to csv")
		operation_time = time.time()
 
		ids = []
		n_items = []
		terms = []
		created_at = []
		last_activity= []
		root_user = []
		root_user_created_at = []
		root_user_followers = []
		root_item = []
		other_items = []
		
		ordered_clusters = self.get_sorted_clusters_by_items()
		
		for cluster in ordered_clusters[:settings.max_active_clusters]:
			if cluster.n_items>settings.min_items_to_show_cluster:
				ids.append(cluster.id)
				n_items.append(cluster.n_items)				
				terms.append(self.get_relevant_terms(cluster))
				created_at.append(cluster.created_at)				
				last_activity.append(cluster.last_activity)
				root_user.append(cluster.items[0].user)
				if settings.source=="twitter":
					root_user_created_at.append(cluster.items[0].user_created_at)
					root_user_followers.append(cluster.items[0].user_followers)
				else:
					root_user_created_at.append("-")
					root_user_followers.append("-")
				root_item.append(cluster.items[0].content)
				other_items.append([item.user+"\n"+str(item.created_at)+"\n"+item.content+"\n*****************************\n"for item in cluster.items])

		data = pd.DataFrame({"id":ids,
							"n_items":n_items, 
							"terms":terms,
							"created_at":created_at,
							"last_activity":last_activity,
							"root_user":root_user,
							"root_user_created_at":root_user_created_at,
							"root_followers":root_user_followers,
							"root_item":root_item,
							"other_items":other_items})

		data.to_csv(settings.active_clusters_csv, mode="w", header=True, encoding='utf-8')
		self.debug.log("\tFinished in: "+str(time.time()-operation_time))
		self.debug.log("<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>")

	def store(self, cluster):

		root_user_created_at = []
		root_user_followers = []

		if settings.source=="twitter":
			root_user_created_at.append(cluster.items[0].user_created_at)
			root_user_followers.append(cluster.items[0].user_followers)
		else:
			root_user_created_at.append("-")
			root_user_followers.append("-")
		terms = self.get_relevant_terms(cluster)
		other_items = []
		other_items.append([item.user+"\n"+item.content+"\n*****************************\n" for item in cluster.items])

		data = {"id_str":cluster.id,
				"n_items":cluster.n_items,
				"terms":terms,
				"created_at":cluster.created_at,
				"last_activity":cluster.last_activity,
				"root_user":cluster.items[0].user,
				"root_user_created_at":root_user_created_at,
				"root_followers":root_user_followers,
				"root_item":cluster.items[0].content,
				"other_items":other_items}
		self.table.insert(data)	