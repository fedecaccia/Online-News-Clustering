import settings
import dataset
import datafreeze

db = dataset.connect(settings.clusters_db)
result = db[settings.store_clusters_table].all()
datafreeze.freeze(result, format='csv', filename=settings.dump_clusters_csv)