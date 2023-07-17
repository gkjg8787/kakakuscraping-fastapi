
from urllib.parse import urlencode

class SurugayaURL:
    def __init__(self, rsopts):
        self.base = 'https://www.suruga-ya.jp/search'
        self.query = { 'category':''
                        ,'search_word': ''
                        ,'is_marketplace':0
                        ,'ch':'true'
                        ,'inStock':'On'
                         }
        self.rsopts = rsopts
        self.isExistCate = True
    
    def setParameter(self, param):
        self.isExistCate = True
        if 'category' in param:
            opts = self.rsopts.getOptions()
            idtable = opts['category']['surugaya']['idtable']
            self.inCategoryTable(idtable, str(param['category']))
        
        if 'page' in param:
            try:
                num = int(param['page'])
                if num > 0 :
                    self.setPage(num)
            except ValueError:
                pass
        
        if 'zaiko' in param:
            try:
                num = int(param['zaiko'])
                if num == 1:
                    self.setStock('Off')
            except ValueError:
                pass
    
    def setStock(self, val):
        self.query['inStock'] = val
    
    def setPage(self, num):
        self.query['page'] = num
    
    def inCategoryTable(self, table, val):
        if not val in table: 
            self.isExistCate = False
            return
        num = table[val]
        if len(num) != 0:
            self.setCategory(num)

    
    def setCategory(self,num):
        self.query['category'] = num

    def setMarketPlace(self, num):
        self.query['is_marketplace'] = num
    
    def setWord(self, word):
        self.query['search_word'] = word

    def createURL(self):
        url = '%s?%s' % (self.base, urlencode(self.query))
        return url

    def isExistCategory(self):
        return self.isExistCate

 