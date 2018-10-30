import settings
import datetime
import pandas as pd

class Chrono(object):

	"""Chrono: Shows the time that last item was created, in backtesting or online mode"""

	def __init__(self):
		self.last_update = pd.to_datetime(settings.initial_time)

	def set_last_update(self, date):
		self.last_update = date

	def get_utc_time(self):
		if settings.online:
			return datetime.datetime.utcnow()            
		else:
			return self.last_update
			