import settings
from csv_loader import Loader
from scraper import NewsScraper, TwitterScraper
import time

class Source(object):

    """Source: Select right source for the problem"""

    def __init__(self, debug):
        operation_time = time.time()
        if settings.online == True:
            debug.log("ONLINE SCRAPER")
            debug.log("Initializing workers...")            
            if settings.source == "news":
                self.source = NewsScraper()
            elif settings.source == "twitter":
                self.source = TwitterScraper()
            elif settings.source == "reddit":
                debug.log("Reddit scraper is not implemented yet")
                exit()
            else:
                debug.log("Bad 'source' word")
                exit()
            self.source.listen()
        else:
            debug.log("BACKTESTING")
            debug.log("Reading csv data...")
            self.source = Loader()
        debug.log("\tFinished in: " +str(time.time()-operation_time))
    
    def get_source(self):
        return self.source