from typing import Dict

class SearchCmn:
    PAGE = 'page'
    ENABLE = 'enable'
    MIN = 'min'
    MAX = 'max'
    MOREPAGE = 'more'
    TRUE = 'true'
    FALSE = 'false'
    CURRENT = 'current'

class SearchParser:
    ITEMS = 'items'
    STORENAME = 'storename'
    TITLE = 'title'
    TITLE_URL = 'titleURL'
    CATEGORY = 'category'
    NEW = 'new_price'
    USED = 'used_price'
    PRICE = 'price'
    SINAGIRE = 'sinagire'
    IMAGE_URL = 'imageURL'
    IMAGE_ON_ERR = 'imageOnError'
    STATE = 'state'
    YOYAKU = 'yoyaku'
    SUBINFO = 'subinfo'
    ZAIKO = 'zaiko'
    MAILBIN = 'mailbin'
    MAKEPURE = 'makepure'
    MAKEPURE_BIKO = 'makepurebiko'
    MAKEPURE_URL = 'makepureURL'
    PAGE = SearchCmn.PAGE
    ENABLE = SearchCmn.ENABLE
    MIN = SearchCmn.MIN
    MAX = SearchCmn.MAX
    MOREPAGE = SearchCmn.MOREPAGE
    TRUE = SearchCmn.TRUE
    FALSE = SearchCmn.FALSE

    def __init__(self):
        self.allitem :Dict = {}

    def getItems(self):
        return self.allitem[self.ITEMS]
    
    def getPage(self):
        return self.allitem[self.PAGE]
    
    def delspace(self, text):
        return text.replace(' ','')

    def trimStr(self,text):
        table = str.maketrans({
                            '\u3000':'',
                            '\n':'',
                            '\xa0':''
                              })
        return text.translate(table).strip()
    
    def htmlTrim(self, text):
        text = self.delspace(text)
        text = self.trimStr(text)
        return text
    
