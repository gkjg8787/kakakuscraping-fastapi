from urllib.parse import urlencode

class BookoffURL:
    def __init__(self, rsopts):
        self.base = 'https://www.bookoffonline.co.jp/display/'
        self.fixword = 'L001'
        self.comma_query = { 'st':'a'
                         }
        self.search_word = { 'q' : '' }
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
        self.comma_query['st'] = 'z'
    
    def setPage(self, num):
        self.comma_query['p'] = num
    
    def inCategoryTable(self, table, val):
        if not val in table: 
            self.isExistCate = False
            return
        num = table[val]
        if len(num) != 0:
            self.setCategory(num)

    
    def setCategory(self,num):
        self.comma_query['bg'] = num

    def setWord(self, word):
        self.search_word['q'] = word
    
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
        url = '%s%s' % (self.base, self.fixword)
        url += self.joinCommaQuery()
        if len(self.query) > 0:
            url = '%s&%s' % (url, urlencode(self.query))
        return url

    def isExistCategory(self):
        return self.isExistCate