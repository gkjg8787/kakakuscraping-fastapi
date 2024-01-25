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
            jfile = open(fpath, "r", encoding="utf-8")
            text = json.load(jfile)
            jfile.close()
            return text
        except FileNotFoundError:
            pass
        finally:
            jfile.close()

        return text

    def getOptions(self):
        return self.opts
