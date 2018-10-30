import settings
import dataset
import datafreeze

db = dataset.connect(settings.scraper_db)
result = db[settings.tweets_table].all()
datafreeze.freeze(result, format='csv', filename=settings.dump_tweets_csv)