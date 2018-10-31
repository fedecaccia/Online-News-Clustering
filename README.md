# Online News Clustering

This program performs an incremental clustering algorithm over news and social media articles. It can be used to quickly and efficiently detect bursting topics on internet.

## Dependencies

The main code can be independently run on python 2 or python 3, but some few lines only run on python2. This is because it uses [Dragnet](https://github.com/seomoz/dragnet) library to extract content of html sites. To run it on python 3, be sure that Dragnet importations are disabled and also change `Queue` importation with `queue`.
The programs uses the following libraries listed on requeriments.txt:

- [Datafreeze](https://github.com/pudo/datafreeze)

- [Dataset](https://dataset.readthedocs.io/en/latest/)

- [Dragnet](https://github.com/seomoz/dragnet) (dragnet should be installed following instructions from github site)

- [FeedParser](https://pythonhosted.org/feedparser/)

- [Langdetect](https://pypi.org/project/langdetect/)

- [Matplotlib](https://matplotlib.org/)

- [Numpy](http://www.numpy.org/)

- [Spacy](https://spacy.io/)

- [Tweepy](http://www.tweepy.org/)

- [Pandas](https://pandas.pydata.org/)

- [Requests](http://docs.python-requests.org/en/master/)

- [Scikit-learn](http://scikit-learn.org/stable/) (versions before scikit-learn==0.17 have incompatibility with [dataset](https://dataset.readthedocs.io/en/latest/))

- [SciPy](https://www.scipy.org/)

- [SQLAlchemy](https://www.sqlalchemy.org/)

- [TextBlob](http://textblob.readthedocs.io/en/dev/) (*Note: TextBlob uses Google Translation API, which sometimes produces request errors. When this happens, try using langdetect commenting line 165 in workers.py, and uncommenting line 164.*)

To install them type on terminal:

```
pip install -r requirements.txt
```

In order to use Spacy with english words, you have to download the english dicitionary typing:

```
python3 -m spacy download en
```

To use Spacy with in other languages, you have to only change the `en` keyword by the correspondent:

- Dutch: `nl`

- French: `fr`

- German: `de`

- Italian: `it`

- Multi-language: `xx`

- Portuguese: `pt`

- Spanish: `es`

If you need take a look at Spacy [documentation](https://spacy.io/models/).

## Quickstart

To start detecting trending news about some topic, complete the `track_terms.dat` file with terms to filter the articles and provide an `opml` file with the list of feeds to scrape. To start detecting trending tweets, complete the `track_terms.dat` file with terms to filter the publications on twitter (or leave it empty just to read everything). To filter tweets, you also need to previously [create a twitter app](https://apps.twitter.com/) and provide the keys completing `private_default.py` and renaming it as `private.py`. If you don't know how to create a twitter app, theere are some nice tutorials over there, like [this one](https://iag.me/socialmedia/how-to-create-a-twitter-app-in-8-easy-steps/).

Make sure you has propertly installed all the dependencies described before. Also, make sure you have downloaded the Spacy language dictionary you are going to need.

Check that `online` variable is defined True on `settings.py`. Customize other parameters or just leave them with default values for now. You can check their use cases and their possible value in the [User Manual](./user_manual.md).

To start clustering, type on terminal:

```
python2 main.py
```

Once the algorithm has been running for a while, you can plot current cluster results typing on another terminal:

```
python3 cluster_plotter.py
```

## User's manual
The [User's Manual](./user_manual.md) explain how to use the available parameters and define study cases in `settings.py`.

## Main features:

- Execution modes: There are two main modes of execution:
a) Backtesting mode: This mode performs an online clustering over items provided in a `csv` file.
b) Online mode: This mode performs an online clustering over items that are read continuously from different internet sources. You can use the programm to look for news and trending topics on journals, *reddit*, *twitter* and other social media.

- Sources: Choose between *news* and *twitter*. The *news* option enables the lecture of a file containing a list of *feeds* that you are interested.

- Efficient text data representation: Items collected from sources are grouped into buckets. In each bucket we compute a vector representation of each item, wich consist in several steps:
a) Several parameters extraction, like *content*, *publication time* on news, or *content*, *publication time*, *user name*, *user followers* and so many others on tweets.
b) Vector representation of each item using the [bag of words](https://en.wikipedia.org/wiki/Bag-of-words_model) method. This step is implemented using the [CountVectorizer](http://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html) class of [sklearn](http://scikit-learn.org/stable/) library.
c) Removing stop words from count vectors.
d) Stemming step using [spacy](https://spacy.io/) library. 
After obtaining the count representation of each item of the new *bucket*, (and so, having the count representation of all the elements in the *universe*, which consist of *buckets* of items and *clusters* of items), perform the lasts steps:
e) Compute the [tf-idf](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) representation of each item in the *buckets*.
f) Compute [tf-idf](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) representation of each *cluster* centroid.
No library is used for the *tf-idf* calculation. A specific calculation method was developed for this problem, to efficiently manage the structures used and the fact that *new terms* continually appear.

- Efficient text data clustering: Once a *bucket* is processed, each item is compared only with centroids of clusters, which are stored in a [compressed sparse column matrix](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csc_matrix.html) format, which allows us to compute the matrix vector products in an efficient way. If the minimum distance between the item and a cluster is lower than a predefined threshold, the item is assigned to that cluster (and so, the *cluster* centroid is updated). Otherwise, another cluster is created with the item. Although the measured distances are computed between the *tf-idf* representations of items and clusters, the raw count of terms of each cluster is also stored for the later re-calculation of their *tf-idf* representation.

## Improvements:

Three main improvements are performed to increase the speedup of the algorithm and the accurancy of the clustering:

- Term pruning: In tweets and social blogs users usually have spelling errors. Those errors are learned by the model as if they were new terms, but they only appear once or twice and never again. Due to this fact, the dimension of terms grows too much, generating unnecessarily large data structures. To deal with this problem, there are two main approaches: one try to identify and correct before the count representation (a priory) these spelling errors, and the other try to identify after the count representaiton (a posteriori) the similarity between these terms. This program makes use of a second approach called *term similarity analysis* to avoid losing excessive time in data processing. So, misspelled terms are stored as new terms. A *pruning* algorithm has been developed to remove unused terms (misspelled terms become unused over time because it's difficult that different bloggers have the same spelling errors). The *pruning* algorithm can be called with some *frequency* provided by input. The *pruning* step not only remove terms from the learned dictionary of words, it also restructures all necessary data in an efficient way in order to reduce dimensions.
It could be claimed that the time gained in preprocessing is then lost between the a posteriori approach and the pruning step, but the developer has opted for the second approach because it also generates an improvement in the precision of the clustering.

- Inactive clustering remove: The amount of generated clusters increase continuously with time, but some clusters contain isolated items and some others simply became inactive with time. In order to keep in memory only active clusters, we can set by input some parameters that regulate the life of them. Before removing, the algorithm checks whether a cluster has been important or not. Important clusters are stored in SQL format to further analyze them.

- Term similarity analysis: In a paper [1] published last year, the autors have shown that *term similarity analysis* not only deals with the misspelling errors frequently found on blog documents, but also improves the accurancy of the clsutering. The method of *term similarity analysis* computes *similarities* between terms based on *co-ocurrences* between them in different blogs. These calculations are undertood as similarities between concepts. Based on that, a vector expansion algorithm is performed over *cluster* centroids and items from the *bucket* that is going to be clusterized.

Although these algorithms improve the precision of the clustering method, it must be taken into account that they also increase the calculation time. The frequency of its use must be regulated from the input, so that the total clustering calculation time never exceeds the time that each bucket needs to be filled. Otherwise, you will be clustering on increasingly older data.

## References:

[1] [Incremental clustering with vector expansion for online event detection in microblogs](https://www.researchgate.net/publication/320861041_Incremental_clustering_with_vector_expansion_for_online_event_detection_in_microblogs), Ozer Ozdikis, Pinar Karagoz and Halit Oğuztüzün, October 2017.