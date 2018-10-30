#############################################################
# GENERAL
#############################################################

# DEBUG
debug = True

# MODE
online = True

# BACKTESTING SOURCE
source_csv="test_tweets.csv"

# CHRONO
initial_time = "2018-04-09 18:30" # works on tweet csv
import datetime
initial_time = datetime.datetime.utcnow()

#############################################################
# SCRAPER
#############################################################

# SOURCE: "twitter" - "news" - "reddit"
source = "news"
reddit = False

# SCRAPER
track_terms_file = "track_terms.dat"
scraper_db = "sqlite:///crypto.db"
language = "en"

## TWITTER SCRAPER
download_retweets=True
cluster_retweets=True
check_tweet_user_creator=False
new_clusters_min_followers=0
twitter_account_file="valid_twitter_users.dat"
tweets_table = "crypto_tweets"
dump_tweets_csv="tweets_database.csv"

# NEWS SCRAPPER
news_feed_file = "newsfeeds.opml"
news_table = "crypto_news"
dump_news_csv="news_database.csv"

#############################################################
# PRE-PROCESSING
#############################################################

# BUCKETS OPTIONS
n_look_ahead_buckets = 1
bucket_history = 3
min_items_per_bucket = 5
min_time_per_bucket = 0 # [secs]
extra_stop_words_file="stop_words.dat"

# ITEMS
historic_window = 60*60*24 # [secs] 1 days
min_user_life = 60*60*24 # [secs] 1 month (only valid with twitter)
min_user_followers = 300  # (only valid with twitter)

# PRE-CLUSTERING WORK
tsa = True
term_similarity_count = 50
term_similarity_threshold = 0.5

#############################################################
# CLUSTERING
#############################################################

# CLUSTERING ALGORITHM
update_centroids_while_clustering = True
merge_threshold = 0.3

#############################################################
# POST-PROCESSING
#############################################################

# POST-CLUSTERING WORK
pruning = True
pruning_frequency = 5 # buckets

# PLOTTING
min_items_to_show_cluster = 2
max_active_clusters = 50
max_active_clusters_to_debug = 3
show_items = False
active_clusters_csv = "active_clusters.csv"
cluster_max_inactive_life = 60*60*24
clusters_db = "sqlite:///clusters.db"
store_clusters_table = "active_clusters"
dump_clusters_csv = "stored_clusters.csv"

#############################################################
# OTHERS
#############################################################

# Do not change these lines

with open(twitter_account_file) as accounts:    
    valid_twitter_users = accounts.readlines()
valid_twitter_users = set([x.strip() for x in valid_twitter_users])

with open(extra_stop_words_file) as stop_file:    
    extra_stop_words = stop_file.readlines()
extra_stop_words = set([x.strip() for x in extra_stop_words])

with open(track_terms_file) as terms_file:    
    track_terms = terms_file.readlines()
track_terms = set([x.strip() for x in track_terms])