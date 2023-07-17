
import os
from pathlib import Path
import time
import hashlib
import glob

from common import read_config
from cache.rwcache import RWCache

class FileCache(RWCache):
    HASHFILE_EXT = ".hf"

    def __init__(self, group=''):
        self.group = group
    
    def read(self, title):
        hd = self.hasHashData(title)
        if len(hd) > 0 and \
            not self.expireHashData(title):
            return hd
        return ''

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
        return hashlib.md5(title.encode('utf-8')).hexdigest()
    
    def getHashFileName(self, ht):
        if len(self.group) == 0:
            return ht + self.HASHFILE_EXT
        return self.group + ':' + ht + self.HASHFILE_EXT
    
    def getCacheDir(self):
        return read_config.get_dl_temp_dir()
    
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
        return ''
    
    def getHashFileTimeStamp(self, ht):
        return os.stat(self.getHashPath(ht)).st_mtime
    
    def fullHashDataNum(self):
        cachedir = self.getCacheDir()
        pl = list(Path(cachedir).glob(self.getHashFileName('*')))
        cache_max_num = int(read_config.get_cache_max_num())
        if len(pl) >= cache_max_num:
            pl.sort(key=os.path.getmtime)
            for i in range(len(pl)-cache_max_num+1):
                os.remove(pl[0])
                pl.pop(0)
    
    def expireHashData(self, title):
        ht = self.createHash(title)
        f_ut = self.getHashFileTimeStamp(ht)
        ut_now = time.time()
        elapsed_time = ut_now - f_ut
        cache_time = int(read_config.get_cache_time())
        if elapsed_time > cache_time:
            self.deleteHashData(ht)
            return True
        else:
            return False