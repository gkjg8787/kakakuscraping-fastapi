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
        q = r'.productInformation__stock__alert'
        elem = soup.select(q)
        if len(elem) == 0:
            return True
        return False
    
    def parseTitle(self, soup):
        q = r'.productInformation__title'
        elem = soup.select(q)
        title = self.trimStr(str(elem[0].text))
        return title
    
    def parsePrice(self, soup, iteminfo):
        elem = soup
        price = self.parseCommonPrice(elem)
        if not self.parseUsedPrice(elem, iteminfo, price):
            self.parseNewPrice(elem, iteminfo, price)
        iteminfo.taxin = self.getTaxin(elem)
    
    def parseCommonPrice(self, soup):
        q = r'.productInformation__price--large'
        elem = soup.select(q)
        ptn = r'([1-9][0-9,]+)'
        for e in elem:
            m = re.findall(ptn, e.text)
            if len(m) == 0: continue
            return int(m[0].replace(',', ''))
        return None

    def parseUsedPrice(self, soup, iteminfo, price):
        if not price:
            return False
        q = r'.productInformation__Btn__used.-active'
        elem = soup.select_one(q)
        if elem:
            iteminfo.usedPrice = int(price)
            return True
        return False

        
    
    def parseNewPrice(self, soup, iteminfo, price):
        if not price:
            return False
        q = r'.productInformation__Btn__new.-active'
        elem = soup.select_one(q)
        if elem:
            iteminfo.newPrice = int(price)
            return True
        return False
    
    def getTaxin(self, elem):
        return True
 

    def getItems(self):
        return (self.iteminfo,)
    
    

