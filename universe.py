import settings
import time
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.preprocessing import normalize
from itertools import count

class Universe(object):

    """Universe: Universal variables like global terms and global frequencies"""

    def __init__(self, debug):
        self.debug = debug
        self.n_items = 0
        self.terms_positions = dict()
        self.n_terms = 0
        self.df = np.array([])
        self.log_n_df = np.array([])
        self.step = 0
        self.ordered_list_of_terms = []

    def increase_items(self):
        self.n_items+=1

    def remove_n_items(self, n):
        self.n_items-=n

    def remove_df(self, removing_df):
        self.df -= removing_df

    def update_terms(self, terms):
        for term in terms:
            if term not in self.terms_positions:
                self.terms_positions[term] = self.n_terms
                self.n_terms += 1
                self.df = np.append(self.df, 1)
                self.ordered_list_of_terms.append(term)
            else:
                term_position = self.terms_positions[term]
                self.df[term_position] += 1
    
    def get_universal_item_counts(self, terms, counts):
        universal_count = sparse.dok_matrix((self.n_terms, 1))
        for term, count in zip(terms, counts):
            term_position = self.terms_positions[term]
            universal_count[term_position, 0] = count
        return universal_count

    def get_universal_tfidf(self, universal_count):
        tfidf = universal_count.T.multiply(self.log_n_df).T
        tfidf = normalize(tfidf, norm='l2', axis=0)
        return tfidf

    def compute_log_n_df(self):
        self.debug.log("Computing log_n_df...")
        operation_time = time.time()
        self.log_n_df = np.log(self.n_items/self.df)
        # warning by zero division, tweets with this terms are not more active
        self.log_n_df[self.df==0] = 0
        # log(1)=0 !!!
        self.log_n_df[self.df==self.n_items] = 0
        self.debug.log("\tFinished in: "+str(time.time()-operation_time))
        self.debug.log("\tlog_n_df shape: "+str(self.log_n_df.shape))

    def prune_terms(self, clusters):
        self.step += 1
        if settings.pruning and self.step % settings.pruning_frequency == 0:
            self.debug.log("Pruning terms...")
            operation_time = time.time()

            terms_to_remove_positions = np.where(self.df == 0)[0]
            self.remove_terms(terms_to_remove_positions)
            clusters.remove_terms(terms_to_remove_positions)

            self.debug.log("\tFinished in: "+str(time.time()-operation_time))

    def remove_terms(self, terms_to_remove_positions):
        self.debug.log("\tRemoving "+str(len(terms_to_remove_positions))+" term positions from universal df...")
        self.debug.log("\tInitial shape:"+str(self.df.shape))
        self.df = np.delete(self.df, terms_to_remove_positions)
        self.debug.log("\tFinal shape:"+str(self.df.shape))

        self.debug.log("\tRemoving "+str(len(terms_to_remove_positions))+" terms from ordered list of terms...")
        self.debug.log("\tInitial shape:"+str(len(self.ordered_list_of_terms)))
        self.ordered_list_of_terms = list(np.delete(self.ordered_list_of_terms, terms_to_remove_positions))
        self.debug.log("\tFinal shape:"+str(len(self.ordered_list_of_terms)))

        self.terms_positions = {key:val for key, val in zip(self.ordered_list_of_terms, count())}
        self.debug.log("\tFinal lenght of list of terms: "+str(len(self.ordered_list_of_terms)))

        self.n_terms = len(self.terms_positions)
        self.debug.log("\tFinal amount of terms: "+str(self.n_terms))