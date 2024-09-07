import json

class Settings:
    data = {}
    def __init__(self):
        """
        Get settings.json values
        """
        with open("settings.json", "r") as file:
            self.data = json.load(file)

    def get(self,name):
        try:
            return self.data[name]
        except:
            return None