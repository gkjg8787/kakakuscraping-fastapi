from urllib.parse import quote

class GeoURL:
    def __init__(self, rsopts):
        self.base = 'https://ec.geo-online.co.jp/shop/goods/search.aspx'
        self.simple_query = {   'search': 'x'
                        ,'keyword':''
                        ,'submit1':'送信'
                         }
        self.query = {
                        'search.x':0
                        ,'keyword':''
                        }
        self.rsopts = rsopts
        self.isExistCate = True
    
    def setParameter(self, param):
        self.isExistCate = True
        if 'category' in param:
            opts = self.rsopts.getOptions()
            idtable = opts['category']['geo']['idtable']
            self.inCategoryTable(idtable, str(param['category']))
        
        if 'page' in param:
            try:
                num = int(param['page'])
                if num > 0 :
                    self.setPage(num)
            except ValueError:
                pass
    
    
    def setPage(self, num):
        self.query['p'] = num
    
    def inCategoryTable(self, table, val):
        if not val in table: 
            self.isExistCate = False
            return
        num = table[val]
        if len(num) != 0:
            self.setCategory(num)

    
    def setCategory(self,num):
        self.query['tree'] = num

    def setWord(self, word):
        self.query['keyword'] = word
    
    def joinQuery(self, dic):
        ret = ''
        for k in dic:
            if len(ret) > 0:
                ret += '&'
            ret += '%s=%s' % (k, quote(str(dic[k]), encoding='shift_jis'))
        return ret

    def createURL(self):
        url = '%s?%s' % (self.base, self.joinQuery(self.query))
        return url

    def isExistCategory(self):
        return self.isExistCate