
import re
from html_parser import htmlparse
from bs4 import BeautifulSoup


class NetoffParse(htmlparse.ParseItems):
    def __init__(self, fp, id, date, url):
        self.soup = BeautifulSoup(fp, "html.parser", from_encoding='utf-8')
        self.iteminfo = htmlparse.ParseItemInfo()
        self.iteminfo.id = id
        self.iteminfo.timeStamp = date
        self.iteminfo.url = url
        self.iteminfo.storename = "ネットオフ"
        self.parseItem(self.soup, self.iteminfo)
        
    
    def parseItem(self, soup, iteminfo):
        iteminfo.isSuccess = self.parseSuccess(soup)
        if not iteminfo.isSuccess:
            return
        iteminfo.name = self.parseTitle(soup)
        if not self.existZaiko(soup):
            iteminfo.isSuccess = False
            return
        self.parsePrice(soup, iteminfo)
        self.parseOnSale(soup, iteminfo)
    
    def parseSuccess(self, soup):
        q = r'.titleArea'
        elem = soup.select(q)
        if len(elem) == 0:
            return True
        ptn = r'【現在ご利用いただけません】'
        if ptn in str(elem[0]):
            return False
        return True
    
    def existZaiko(self, soup):
        q = r'.iStock'
        elem = soup.select(q)
        if len(elem) == 0:
            return False
        return True
    
    def parseTitle(self, soup):
        q = r'.descriptionIn h2'
        elem = soup.select(q)
        ptn = r'<h2>(<span class="free_shipping_red">送料無料</span>)?\t\t([\s\S]+)(<span)'
        m = re.findall(ptn, self.trimStr(str(elem[0])))
        return m[0][1]
    
    def parsePrice(self, soup, iteminfo):
        q = r'.descriptionIn'
        elem = soup.select(q)
        #if not self.isUsed(elem): return
        iteminfo.usedPrice = int(self.getPrice(elem))
        iteminfo.taxin = self.getTaxin(elem)
    
    def isUsed(self, elem):
        #一律中古扱い
        return True
    
    def getPrice(self, elem):
        yen = r'.price_text2'
        pricetag = elem[0].select(yen)
        ptext = pricetag[0].text.replace(',','')
        ptn = r'[1-9][0-9]*'
        m = re.findall(ptn, ptext)
        return int(m[0])

    def getTaxin(self, elem):
        q = r'.price_text2 .price_text_small'
        tax = elem[0].select(q)
        for s in tax:
            if '(税込)' in s:
                return True
        
        return False
    
    def parseOnSale(self, soup, iteminfo):
        q = r'.itemInfo .sale_balloon'
        elem = soup.select(q)
        if len(elem) == 0:
            return
        iteminfo.onSale = True
        name = elem[0].select('p')
        iteminfo.saleName = name[0].text

    def getItems(self):
        return (self.iteminfo,)
    

