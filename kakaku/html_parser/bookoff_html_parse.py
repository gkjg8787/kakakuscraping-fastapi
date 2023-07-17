import re
from html_parser import htmlparse
from bs4 import BeautifulSoup


class BookoffParse(htmlparse.ParseItems):
    def __init__(self, fp, id, date, url):
        self.soup = BeautifulSoup(fp, "html.parser", from_encoding='utf-8')
        self.iteminfo = htmlparse.ParseItemInfo()
        self.iteminfo.id = id
        self.iteminfo.timeStamp = date
        self.iteminfo.url = url
        self.iteminfo.storename = "ブックオフ"
        self.parseItem(self.soup, self.iteminfo)
        
    
    def parseItem(self, soup, iteminfo):
        iteminfo.isSuccess = True
        iteminfo.name = self.parseTitle(soup)
        if not self.existZaiko(soup):
            iteminfo.isSuccess = False
            return
        self.parsePrice(soup, iteminfo)
    
    def existZaiko(self, soup):
        q = r'#buttongroup .nosotck'
        elem = soup.select(q)
        if len(elem) == 0:
            return True
        return False
    
    def parseTitle(self, soup):
        q = r'#ttlArea h1'
        elem = soup.select(q)
        title = self.trimStr(str(elem[0].text))
        return title
    
    def parsePrice(self, soup, iteminfo):
        q = r'#itemdet'
        elem = soup.select(q)
        #if not self.isUsed(elem): return
        self.parseUsedPrice(elem[0], iteminfo)
        self.parseNewPrice(elem[0], iteminfo)
        iteminfo.taxin = self.getTaxin(elem)
    
    def parseUsedPrice(self, soup, iteminfo):
        q = r'#spec .oldprice'
        elem = soup.select(q)
        ptn = r'￥([1-9][0-9,]+)'
        for e in elem:
            m = re.findall(ptn, e.text)
            if len(m) == 0: continue
            iteminfo.usedPrice = int(m[0].replace(',', ''))
            return
    
    def parseNewPrice(self, soup, iteminfo):
        q = r'#spec .mainprice'
        elem = soup.select(q)
        ptn = r'￥([1-9][0-9,]+)'
        for e in elem:
            m = re.findall(ptn, e.text)
            if len(m) == 0: continue
            iteminfo.newPrice = int(m[0].replace(',', ''))
            return
    
    def getTaxin(self, elem):
        q = r'#spec .price_tax'
        tax = elem[0].select(q)
        for s in tax:
            if '（税込）' in s:
                return True
        
        return False

    def getItems(self):
        return (self.iteminfo,)
    
    

