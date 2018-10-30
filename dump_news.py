import settings
import dataset
import datafreeze

db = dataset.connect(settings.scraper_db)
result = db[settings.news_table].all()
datafreeze.freeze(result, format='csv', filename=settings.dump_news_csv)