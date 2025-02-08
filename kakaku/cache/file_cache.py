import os
from pathlib import Path
import time
import hashlib
import glob
import datetime

from common import util as cm_util
from cache.rwcache import RWCache


class FileCache(RWCache):
    HASHFILE_EXT = ".hf"
    group: str
    cachedir: str
    cache_max_num: int
    cache_time: int
    span_over_days: bool

    def __init__(
        self,
        cachedir: str,
        cache_max_num: int,
        cache_time: int,
        group: str = "",
        span_over_days: bool = True,
    ):
        self.group = group
        self.cachedir = cachedir
        self.cache_max_num = cache_max_num
        self.cache_time = cache_time
        self.span_over_days = span_over_days

    def read(self, title):
        hd = self.hasHashData(title)
        if len(hd) > 0 and not self.expireHashData(title):
            return hd
        return ""

    def write(self, title, value):
        self.fullHashDataNum()
        ht = self.createHash(title)
        self.createHashData(ht, value)
        return

    def remove_all(self):
        for f in self.get_hash_files():
            os.remove(f)

    def get_hash_files(self):
        files = glob.glob(os.path.join(self.getCacheDir(), f"*{self.HASHFILE_EXT}"))
        return files

    @staticmethod
    def createHash(title):
        return hashlib.md5(title.encode("utf-8")).hexdigest()

    def getHashFileName(self, ht):
        if len(self.group) == 0:
            return ht + self.HASHFILE_EXT
        return self.group + ":" + ht + self.HASHFILE_EXT

    def getCacheDir(self):
        return self.cachedir

    def getHashPath(self, ht):
        cachedir = self.getCacheDir()
        return os.path.join(cachedir, self.getHashFileName(ht))

    def createHashData(self, ht, text):
        f = open(self.getHashPath(ht), mode="w")
        f.write(text)
        f.close()

    def existHashData(self, ht):
        return os.path.isfile(self.getHashPath(ht))

    def getHashData(self, ht):
        f = open(self.getHashPath(ht))
        text = f.read()
        f.close()
        return text

    def deleteHashData(self, ht):
        os.remove(self.getHashPath(ht))

    def hasHashData(self, title):
        ht = self.createHash(title)
        if self.existHashData(ht):
            return self.getHashData(ht)
        return ""

    def getHashFileTimeStamp(self, ht):
        return os.stat(self.getHashPath(ht)).st_mtime

    def fullHashDataNum(self):
        cachedir = self.getCacheDir()
        pl = list(Path(cachedir).glob(self.getHashFileName("*")))
        if len(pl) >= self.cache_max_num:
            pl.sort(key=os.path.getmtime)
            for i in range(len(pl) - self.cache_max_num + 1):
                os.remove(pl[0])
                pl.pop(0)

    def expireHashData(self, title):
        ht = self.createHash(title)
        f_ut = self.getHashFileTimeStamp(ht)
        if not self.span_over_days:
            modified_time = datetime.datetime.fromtimestamp(f_ut)
            now = datetime.datetime.now(datetime.timezone.utc)
            now = cm_util.utcTolocaltime(now)
            if modified_time.date() < now.date():
                return True
        ut_now = time.time()
        elapsed_time = ut_now - f_ut
        if elapsed_time > self.cache_time:
            self.deleteHashData(ht)
            return True
        else:
            return False
