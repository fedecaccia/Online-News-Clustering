import settings
import datetime

class Debugger(object):

    """Debugger: Log strings"""

    def __init__(self):
        pass

    def log(self, msg):
        if settings.debug:
            print("["+str(datetime.datetime.now())+"] "+msg)