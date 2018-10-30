# User Manual

This guide describes how to propertly use the program.
All the parameters used by the scrapers, the data pre-processing, clustering and post-processing should be set on `settings.py`. To download data from twitter, you should previously [create an app](https://apps.twitter.com/) and provide the keys completing `private_default.py` and renaming it as `private.py`

The settings are divided in different sections:

- General

- Scraper

- Pre-clustering

- Clustering

- Post-clustering


## General

Parameters:

- `debug` [`bool`]: enable or disable log shapes, algorithm steps, time performing and other variables.

- `online` [`bool`]: enable online mode to download news or tweets from internet, or disable it to execute in backtesting mode. In this case, complete these another parameters:

    - `source_csv` [`string`]: name of the csv file provided in backtesting mode. To check the required headers, inspect the default `test_tweets.csv` file.

    - `initial_time` [`string`]: date time to provide an initial time to the algorithm. This is only used when we are using temporal windows to filter the items.

## Scraper

Parameters:

- `source` [`string`]: use *news* to work with general items, *twitter* to enable Twitter scraper (only using `online`=`True`), and perform spetial treatment such as filtering by tweets by user amount of followers, user account creation time, and others.

- `reddit` [`bool`]: use `True` to enable scrap on reddit and `False` to disable. Take into account that scrapping reddit content could return incorrect data. To perform a detailed scraping on reddit, please perform an specific `RedditScraper` class on `Scraper.py` file, or just modify the `PageWorker` class on `workers.py` file in order to give spetial treatment to the reddit posts, using a library different of Dragnet.

- `track_terms_file` [`string`]: name of the file containing terms to filter items.

- `scraper_db` [`string`]: path to the database to store items.

- `language` [`string`]: choose between `en`, `nl`, `fr`, `de`, `it`, `xx`, `pt` and `es`. Be sure to previously downloaded the required dictionary (see README.md).

Special Twitter parameters:

- `download_retweets` [`bool`]: enable or disable downloading retweets and store in database.

- `cluster_retweets` [`bool`]: enable or disable clusternig retweets.

- `check_tweet_user_creator` [`bool`]: enable or disable filtering tweets by user creator. In `True` case, provide a list of accepted users in a file, and set the name of the file in `twitter_account_file`.

- `twitter_account_file` [`string`]: name of the file containing twitter user accounts accepted.

- `tweets_table` [`string`]: name of the table in which tweets are stored.

- `dump_tweets_csv` [`string`]: name of the csv file to dump tweets using `dump_tweets.py`.

Special news parameters:

- `news_feed_file` [`string`]: name of the file containing the list of feedsused by the scraper.

- `news_table` [`string`]: name of the table in which news are stored.

- `dump_news_csv` [`string`]: name of the csv file to dump news using `dump_news.py`.

## Pre-clustering

Bucket options:

- `n_look_ahead_buckets` [`int`]: number of new buckets to load on the chain of buckets before clustering the current bucket. This is used when the *term similarity analysis* is enabled.

- `bucket_history` [`int`]: total amount of buckets to keep on the bucket of chains.

- `min_items_per_bucket` [`int`]: minimum amount of items per bucket.

- `min_time_per_bucket` [`int`]: minimum amount of time loeading each bucket.

- `extra_stop_words_file` [`string`]: name of the file containing the stop words.

Item options:

- `historic_window` [`int`]: temporal window in seconds to look behind looking for items.

- `min_user_life` [`int`]: minimum amount of time in seconds of the tweet creator that are taking into account in the clustering process.

- `min_user_followers` [`int`]: minimum amount of followers of the tweet creator that are taking into account in the clustering process.

Term similarity analysis:

- `tsa` [`bool`]: enable or disable vector expansion due to term similarity analysis.

- `term_similarity_count` [`int`]: maximum amount of similarity to take into account in each step.

- `term_similarity_threshold` [`float`]: minimum value of similarities between terms to take them as similar.

## Clustering

Parameters:

- `update_centroids_while_clustering` [`bool`]: enable udpating cluster centroids while merging new items into old clusters.

- `merge_threshold` [`float`]: minimum distance accepted betwen an item and a cluster to merge them together.

## Post-clustering

Parameters:

- `pruning` [`bool`]: enable or disable the pruning step.

- `pruning_frequency` [`int`]: in case that pruning is enabled, set the amount of steps beetween prunging steps.

- `min_items_to_show_cluster` [`int`]: minimum amount of items that a cluster must have to be shown as a bursting cluster.

- `max_active_clusters` [`int`]: maximum amount of clusters to show as active clusters per step.

- `max_active_clusters_to_debug` [`int`]: maximum amount of clusters to debug per step.

- `show_items` [`bool`]: enable or disable showing clusters while debugging.

- `active_clusters_csv` [`string`]: name of the file to save current active clusters. This file could then be read by `cluster_plotter.py` in order to plot the results.

- `cluster_max_inactive_life` [`int`]: maximum amount of time in seconds to consider a cluster being active after the last activity. Once inactive, the cluster is removed, and stored if 

- `clusters_db` [`string`]: path to the database to store inactive clusters once removed..

- `store_clusters_table` [`string`]: name of the table to store inactive clusters once removed.

- `dump_clusters_csv` [`string`]: name of the csv file to dump inactive stored clusters using `dump_clusters.py`.