import settings
import pandas as pd

class Loader(object):
    
    """Loader: Load data from a csv file"""

    def __init__(self):
        self.data = self.load_data()
        self.item_index = 0

    def load_data(self):
        if settings.source == "twitter":
            data = pd.read_csv(filepath_or_buffer=settings.source_csv,
                                usecols=["id", "text", "created", "user_name", "user_followers", "user_created"])
        else:
            data = pd.read_csv(filepath_or_buffer=settings.source_csv,
                                usecols=["id", "text", "created", "user_name"])
        data.set_index("id", inplace=True)
        data["created"] = data["created"].apply(lambda x: (pd.to_datetime(x)))
        return data
    
    def get_item(self):
        item = dict()
        try:
            item["id"] = self.data.index[self.item_index]
        except Exception as e:
            print(e)
            raise IndexError("No more items")
        item["created_at"] = self.data.loc[item["id"]]["created"]
        item["content"] = self.data.loc[item["id"]]["text"]
        item["user_name"] = self.data.loc[item["id"]]["user_name"]
        if settings.source == "twitter":
            item["user_followers"] = self.data.loc[item["id"]]["user_followers"]
            item["user_created_at"] = self.data.loc[item["id"]]["user_created"]
        self.item_index+=1
        return item