import json
import os
from common import read_config


class ReadSearchOpt:
    OPT_FNAME = "option.json"

    def __init__(self):
        self.opts = self.readjson()

    def readjson(self):
        fpath = os.path.join(
            read_config.get_search_option_path(), ReadSearchOpt.OPT_FNAME
        )
        text = []
        try:
            with open(fpath, "r", encoding="utf-8") as jfile:
                text = json.load(jfile)
        except FileNotFoundError:
            pass

        return text

    def getOptions(self):
        return self.opts
