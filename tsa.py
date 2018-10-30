import settings
import time
import numpy as np
from scipy import sparse
from sklearn.preprocessing import normalize
# import pystas
# from operator import itemgetter

class TSA(object):

    """TSA: Term symilar analysis to perform vector expansion"""

    def __init__(self, debug, universe, bucket_chain, clusters):
        self.debug = debug
        self.universe = universe
        self.bucket_chain = bucket_chain
        self.clusters = clusters
        self.max_tfidf_pos = None
        self.occurrences = None
        self.co_occurrences = None
        self.similarities = None

    def compute(self):
        if self.are_terms_to_compare():
            self.select_terms_to_compare()
            self.build_buckets_occurence_matrix()
            self.calculate_co_occurrences_matrix()
            self.calculate_similarity_matrix()
            self.select_similarities()
            self.bucket_vector_expansion()
            self.centroids_vector_expansion()

    def are_terms_to_compare(self):
        if self.clusters.centroid_tfidf is not None:            
            return True
        self.debug.log("\tThere are not terms to compare yet...")
        self.bucket_chain.assign_default_vector_expansion()
        return False

    def select_terms_to_compare(self):
        # get max tfidf of each term along clusters
        max_tfidf_val = self.clusters.centroid_tfidf.max(axis=1).T.toarray()[0]
        
        # now get terms with max (tfidf max) values
        self.max_tfidf_pos = np.argsort(max_tfidf_val)[::-1][:settings.term_similarity_count]
        
    def build_buckets_occurence_matrix(self):
        total_items_in_buckets = 0
        for bucket in self.bucket_chain.buckets:
            total_items_in_buckets += bucket.n_items
        l = sparse.lil_matrix((total_items_in_buckets, len(self.max_tfidf_pos)))
        
        row = 0
        for bucket in self.bucket_chain.buckets:
            for item in bucket.items:
                l[row, :] = item.tfidf[self.max_tfidf_pos].T
                row += 1        
        self.occurrences = l.T.tocsc()
        self.occurrences.data = np.ones(len(self.occurrences.data))
        
    def calculate_co_occurrences_matrix(self):
        self.co_occurrences = self.occurrences.dot(self.occurrences.T)
        # normalization by term (and not by cluster)
        self.co_occurrences = normalize(self.co_occurrences, norm='l2', axis=1)
        self.debug.log("\t\toccurences matrix shape: "+str(self.occurrences.shape))
        self.debug.log("\t\tco-occurences matrix shape: "+str(self.co_occurrences.shape))
        
    def calculate_similarity_matrix(self):
        # compute similarities
        self.similarity = self.co_occurrences.dot(self.co_occurrences.T)
        # discount diagonal (auto-similarities)
        self.similarity = self.similarity - sparse.diags(self.similarity.diagonal())
        self.debug.log("\t\tsimilarity matrix shape: "+str(self.similarity.shape))

    # similarities selection current implementation:
    # only one similarity per term, otherwise implement other function
    def select_similarities(self):
        max_sim_val = self.similarity.max(axis=0).toarray()[0]
        max_sim_pos = np.array(self.similarity.argmax(axis=0))[0]
        self.similarities = []
        for iterm, (jterm, s) in enumerate(zip(max_sim_pos, max_sim_val)):
            if s > settings.term_similarity_threshold:
                self.similarities.append([self.max_tfidf_pos[iterm], self.max_tfidf_pos[jterm], s])
        self.similarities.sort(key=lambda x: x[2], reverse=True)
        # self.similarities = sorted(self.similarities, key=itemgetter(2))
        
    def bucket_vector_expansion(self):
        for item in self.bucket_chain.analyzed_bucket.items:
            tfidf = item.tfidf.toarray()
            exp_tfidf = item.tfidf.toarray()
            for sim in self.similarities:
                i = sim[0]
                j = sim[1]
                sij = sim[2]
                # both are valids, but sum just one, the other could be sum j==sim[0]
                exp_tfidf[j] += sij*tfidf[i]
                # exp_tfidf[i] += sij*tfidf[j]
            item.tfidf_expanded = sparse.csc_matrix(exp_tfidf)
        
    def centroids_vector_expansion(self):
        exp_centroids = sparse.dok_matrix((self.clusters.centroid_tfidf.shape[0],
                                            self.clusters.centroid_tfidf.shape[1]))
        for sim in self.similarities:
            i = sim[0]
            j = sim[1]
            sij = sim[2]
            exp_centroids[i] = sij*self.clusters.centroid_tfidf[j]
        self.clusters.centroid_tfidf += exp_centroids.tocsc()