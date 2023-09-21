from urllib.parse import urlencode, quote

class BookoffURL:
    def __init__(self, rsopts):
        self.base = 'https://shopping.bookoff.co.jp/search/'
        self.stock = 'a'
        self.category = None
        self.search_word = ''
        self.query = {}
        self.rsopts = rsopts
        self.isExistCate = True
    
    def setParameter(self, param):
        self.isExistCate = True
        if 'category' in param:
            opts = self.rsopts.getOptions()
            idtable = opts['category']['bookoff']['idtable']
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
                    self.setStock()
            except ValueError:
                pass
    
    def setStock(self):
        #新品、中古在庫あり
        self.stock = 'z'
    
    def setPage(self, num):
        if num == 1:
            return
        self.query['p'] = num
    
    def inCategoryTable(self, table, val):
        if not val in table: 
            self.isExistCate = False
            return
        num = table[val]
        if len(num) != 0:
            self.setCategory(num)

    
    def setCategory(self,num):
        self.category = num

    def setWord(self, word):
        self.search_word = word
    
    def encodeBookoffSJIS(self, val):
        b = val.encode('shift-jis')
        head = '%25'
        ret = ''
        for byte in b:
            ret += '%s%X' % ( head, byte)
        return ret

    def joinCommaQuery(self):
        ret = ',%s' % (urlencode(self.comma_query))
        ret = ret.replace('&', ',')
        ret += ',q=%s' % self.encodeBookoffSJIS(self.search_word['q'])
        return ret
    

    def createURL(self):
        url = '%s/%s/%s' % (self.base, 'stock', self.stock)
        if self.category:
            url = '%s/%s/%s' % (url, 'genre', str(self.category))
        url = '%s/%s/%s' % (url, 'keyword', quote(self.search_word))
        if len(self.query) > 0:
            url = '%s?%s' % (url, urlencode(self.query))
        return url

    def isExistCategory(self):
        return self.isExistCate