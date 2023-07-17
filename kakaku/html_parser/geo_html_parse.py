import re
from html_parser import htmlparse
from bs4 import BeautifulSoup


class GeoParse(htmlparse.ParseItems):
    def __init__(self, fp, id, date, url):
        self.soup = BeautifulSoup(fp, "html.parser", from_encoding='utf-8')
        self.iteminfo = htmlparse.ParseItemInfo()
        self.iteminfo.id = id
        self.iteminfo.timeStamp = date
        self.iteminfo.url = url
        self.iteminfo.storename = "ゲオ"
        self.parseItem(self.soup, self.iteminfo)
        
    
    def parseItem(self, soup, iteminfo):
        iteminfo.isSuccess = self.existPage(soup)
        if not iteminfo.isSuccess:
            return
        iteminfo.name = self.parseTitle(soup)
        self.parsePrice(soup, iteminfo)
        self.parseSale(soup, iteminfo)
    
    def existPage(self, soup):
        q = r'.notice_ p'
        noto = soup.select(q)
        if len(noto) == 0:
            return True
        if '申し訳ございません' in noto[0].text:
            return False
        return True
    
    def parseTitle(self, soup):
        q = r'.goods_name_'
        elem = soup.select(q)
        title = str(elem[0].text).replace('\u3000', ' ')
        return title
    
    def parsePrice(self, soup, iteminfo):
        price = int(self.getPrice(soup))
        if price == -1:
            iteminfo.isSuccess = False
            return

        if self.isUsed(soup):
            iteminfo.usedPrice = price
        else:
            iteminfo.newPrice = price
        iteminfo.taxin = self.getTaxin(soup)
    
    def getPrice(self, soup):
        if not self.isZaiko(soup):
            return -1
        q = r'.goods_price_ .goods_detail_price_'
        elem = soup.select(q)
        ptn = r'([1-9][0-9,]+)円'
        m = re.findall(ptn, self.trimStr(elem[0].text))
        if len(m) == 0:
            return -1
        price = m[0].replace(',', '')
        return price
    
    def isZaiko(self, soup):
        q = r'.cart_btn_list_ li img'
        elem = soup.select(q)
        if len(elem) == 0:
            return True
        for e in elem:
            if 'NoStock' in e['src']:
                return False
        return True
        
    
    def isUsed(self, soup):
        q = r'.goodsspec_ .icon_ .labelSituation'
        elem = soup.select(q)
        if '新品' in elem[0].text:
            return False

        if '状態' in elem[0].text:
            return True

        return False
    
    def getTaxin(self, soup):
        q = r'.goods_detail_price_ .tax_'
        tax = soup.select(q)
        for s in tax:
            if '税込' in s.text:
                return True
        
        return False
    
    def parseSale(self, soup, iteminfo):
        q = r'.goodsspec_ .icon1_ img'
        elem = soup.select(q)
        for e in elem:
            if 'sale.png' in e['src']:
                iteminfo.onSale = True
        
        if not iteminfo.onSale:
            return
        
        q = r'.goodsspec_ .goods_campaign_'
        elem = soup.select(q)
        if len(elem) == 0: return
        iteminfo.saleName = elem[0].text.replace('\u3000', ' ')

    def getItems(self):
        return (self.iteminfo,)
    

