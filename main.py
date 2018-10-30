import time
from debugger import Debugger
from source import Source
from bucket_chain import BucketChain
from clusters import Clusters
from online_clustering import OnlineClustering
from chrono import Chrono
from universe import Universe

def main():

    debug = Debugger()
    chrono = Chrono()
    universe = Universe(debug)
    source = Source(debug).get_source()    
    bucket_chain = BucketChain(debug, chrono, universe, source)
    clusters = Clusters(debug, chrono, universe)
    algorithm = OnlineClustering(debug, universe, bucket_chain, clusters)

    while True:
        operation_time = time.time()
        if bucket_chain.is_updated():
            universe.compute_log_n_df()
            bucket_chain.compute_universal_counts()
            bucket_chain.compute_universal_tfidf()
            clusters.update_centroid_counts()
            clusters.update_centroid_tfidf()
            algorithm.pre_clustering_work()
            algorithm.online_clustering()
            clusters.remove_old_clusters()
            universe.prune_terms(clusters)
            debug.log("BUCKET FINISHED IN: "+str(time.time() - operation_time))
            clusters.debug_active_clusters()
            clusters.save_active_clusters()       

if __name__=="__main__":
    main()