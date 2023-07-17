import re
from html_parser import htmlparse
from bs4 import BeautifulSoup
from abc import ABCMeta, abstractmethod


class AB_SurugayaParse(htmlparse.ParseItems, metaclass=ABCMeta):
    def checkSuccess(self, itemInfo):
        np = int(itemInfo.newPrice)
        up = int(itemInfo.usedPrice)
        if np <= 0 and up <= 0:
            return False
        else:
            return True

class SurugayaProduct_Other(AB_SurugayaParse):
    def __init__(self, soup, id, date, url):
        self.soup = soup
        self.iteminfos = []
        title = self.getTitle(self.soup)
        baseinfo = { 
            'storename':'駿河屋'
            ,'id':id
            ,'title':title
            ,'date':date
            ,'url':url
        }
        self.iteminfos = tuple(self.parseStoreItem(self.soup, baseinfo))
    
    def getItems(self):
        return self.iteminfos
    
    def createParseItemInfo(self, storename, id, title, date, url):
        item = htmlparse.ParseItemInfo()
        item.storename = storename
        item.id = id
        item.name = title
        item.timeStamp = date
        item.url = url
        return item

    def getTitle(self, soup):
        titlebody = "h1.title_product.mgnB15"
        retstr = soup.select_one(titlebody)
        namestr = self.trimStr(retstr.text).replace('の取り扱い店舗一覧','')
        return namestr
    
    def createSinagire(self, binfo):
        return [self.createParseItemInfo(binfo['storename'], binfo['id'], binfo['title']
                ,binfo['date'], binfo['url'])]

    def parseStoreItem(self, soup, binfo):
        retitems = []
        tableq = r'table#tbl_all .item'
        storeitems = soup.select(tableq)
        if len(storeitems) == 0:
            return self.createSinagire(binfo)
        
        for storeitem in storeitems:
            item = self.createParseItemInfo(binfo['storename'], binfo['id'], binfo['title']
                ,binfo['date'], binfo['url'])
            price = self.getPrice(storeitem)
            isNew = self.isNewItem(storeitem)
            storename = self.getStoreName(storeitem)
            if isNew :
                item.newPrice = price
            else :
                item.usedPrice = price
            if len(storename) > 0:
                item.storename = storename
            item.onSale = False
            item.taxin = True
            item.isSuccess = self.checkSuccess(item)
            retitems.append(item)
        return retitems

    def getPrice(self, storeitem):
        pattern = r'<strong class="text-red text-bold mgnL10.+?>(.*?)円'
        m = re.findall(pattern, str(storeitem))
        #print("------------isTblPrice-----------")
        #print(m)
        price = str(m[0]).replace(',', '')
        price = int(re.sub("\\D", "", price))
        return price
    
    def isNewItem(self, storeitem):
        pattern = r'<h2 class="title_product">(.+?)</h2>'
        #print(text)
        m = re.findall(pattern, str(storeitem))
        #print("------------isTblNewUsed-----------")
        #print(m)
        statusstr = self.trimStr(str(m[0]))
        if "新品" in statusstr:
            return True
        return False
    
    def getStoreName(self, storeitem):
        q = r'div.space_text_1.mgnB5 a'
        elem = storeitem.select(q)
        if len(elem) == 0:
            return ''
        storename = elem[0].text
        return storename

class SurugayaProduct(AB_SurugayaParse):
    def __init__(self, soup, id, date, url):
        self.soup = soup
        self.__itemInfo = htmlparse.ParseItemInfo()
        self.__itemInfo.id = id
        self.__itemInfo.timeStamp = date
        self.__itemInfo.url = url
        self.parseTitle(self.soup, self.__itemInfo)
        self.parsePrice(self.soup, self.__itemInfo)
        self.isSale(self.soup, self.__itemInfo)
        self.__itemInfo.isSuccess = self.checkSuccess(self.__itemInfo)
        self.__itemInfo.storename = "駿河屋"
    
    def getItems(self):
        return (self.__itemInfo,)

    def parseTitle(self, soup,itemInfo):
        titlebody = "#item_title"
        retstr = soup.select_one(titlebody)
        namestr = self.trimStr(retstr.text)
        itemInfo.name = namestr
        #print("title:"+namestr)
        return namestr
    
    def parseTaxin(self, text, itemInfo):
        if itemInfo.taxin:
            return 
        if "税込み" in str(text) or "税込" in str(text):
            itemInfo.taxin = True
        
    def parsePrice(self, soup, itemInfo):
        basebody = "div.container_suru.padB40 > .row > .col-8.padL32 .price_group.mb-3 label.mgnB0"
        datal = soup.select(basebody)
        isNew = False
        pattern = '<span.+?buy">(.+?)</span>'
        for val in datal:
            #print(val.text)
            if "新品" in val.text:
                isNew = True
            elif "中古" in val.text:
                isNew = False

            ret = re.findall(pattern, str(val))
            retlen = len(ret)
            if retlen == 0:
                continue
            self.parseTaxin(val.text, itemInfo)    
            if isNew:
                #print("newPrice:"+str(val.text))
                itemInfo.newPrice = int(re.sub("\\D", "", str(ret[0])))
            else:
                #print("usedPrice:"+str(val.text))
                itemInfo.usedPrice = int(re.sub("\\D", "", str(ret[0])))
        
        

    def isSale(self, soup, itemInfo):
        timesalebase = soup.select_one("div.container_suru.padB40 > .row > .col-8.padL32 .flash_sale_title")
        if timesalebase is not None:
            #print("Sale:"+str(timesalebase.text))
            itemInfo.onSale = True
            itemInfo.saleName = self.trimStr(timesalebase.text)
        else:
            itemInfo.onSale = False
    
    def getOrderedDict(self):
        return self.__itemInfo.getOrderedDict()
    
    def getTrendRate(self):
        return self.__itemInfo.getTrendRate()

    def getName(self):
        return self.__itemInfo.name

class SurugayaParse(htmlparse.ParseItems):
    def __init__(self, fp, id, date, url):
        self.soup = BeautifulSoup(fp, "html.parser", from_encoding='utf-8')
        self.__parse = self.createObj(self.soup, id, date, url)

    def createObj(self, soup, id, date, url):
        if "product-other" in str(url):
            return SurugayaProduct_Other(soup, id, date, url)
        else:
            return SurugayaProduct(soup, id, date, url)
    
    def getItems(self):
        return self.__parse.getItems()
    

