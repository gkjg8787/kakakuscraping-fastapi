
import re
from bs4 import BeautifulSoup
from html_parser.search_parser import SearchParser


class SearchBookoff(SearchParser):

        
    def parseSearch(self, htmltext):
        self.soup = BeautifulSoup(htmltext,"html.parser")
        self.allitem[self.ITEMS] = self.parseItems()
        self.allitem[self.PAGE] = self.getPageElem()
    
    def parseItems(self):
        q = r'.js-hoverItem'
        ret = self.soup.select(q)
        sresult = []
        for v in ret:
            itemd ={}
            itemd[self.STORENAME] = "ブックオフ"
            itemd[self.IMAGE_ON_ERR] = "https://content.bookoff.co.jp/images/goods/item_ll.gif"
            self.setTitle(v, itemd)
            self.setImage(v, itemd)
            self.setCategory(v, itemd)
            self.setPrice(v, itemd)
            sresult.append(itemd)
        return sresult


    def allprint(self, htmltext):
        self.parseSearch(htmltext)
        print(self.allitem)
    
    def setTitle(self, elem, itemd):
        titleo = elem.select('.productItem__title')
        itemd[self.TITLE] = titleo[0].text
        itemlink = elem.select('.js-hoverItemLink')
        itemd[self.TITLE_URL] = self.getPerfectURL(itemlink[0]['href'])

    def getPerfectURL(self, url):
        ptn = r'^/'
        m = re.findall(ptn, url)
        if m == None or len(m) == 0: return url
        return 'https://shopping.bookoff.co.jp' + url

    def setCategory(self, elem, itemd):
        cateo = elem.select('.productItem__genreItem--category')
        itemd[self.CATEGORY] = self.htmlTrim(cateo[0].text)

    def setImage(self, elem, itemd):
        imageo = elem.select('.productItem__image img')
        if len(imageo) == 0:
            self.createImageURL(elem, itemd)
            return

        itemd[self.IMAGE_URL] = imageo[0]['src']
    
    def createImageURL(self, elem, itemd):
        itemd[self.IMAGE_URL] = itemd[self.IMAGE_ON_ERR]

    def setPrice(self, elem, itemd):
        price = self.getMainPrice(elem)
        isnew = self.isNewPrice(elem)
        price = price + '円'
        if isnew:
            itemd[self.NEW] = price
        else:
            itemd[self.USED] = price

        self.setSinagire(elem, itemd)

    def getMainPrice(self, elem):
        q = r'.productItem__price'
        priceo = elem.select(q)
        ptn = r'([1-9][0-9,]+)'
        m = re.findall(ptn, self.htmlTrim(priceo[0].text))
        return m[0]
    
    def isNewPrice(self, elem):
        q = r'.productItem__tagList .tagList .tag'
        tro = elem.select(q)
        for tr in tro:
            if '新品' in tr.text:
                return True
            if '中古' in tr.text:
                return False
        return True

    def setSinagire(self, elem, itemd):
        stocko = elem.select('.productItem__stock--alert')
        if len(stocko) != 0:
            itemd[self.SINAGIRE] = '品切れ'
        
    def parsePageNum(self, info):
        q = r'.pagination__page'
        pages = self.soup.select(q)
        if len(pages) == 0:
            return
        pmin = -1
        pmax = -1
        for p in pages:
            v = self.htmlTrim(p.text)
            if pmin == -1:
                pmin = int(v)
                pmax = int(v)
                continue
            if pmin > int(v):
                pmin = int(v)
            if pmax < int(v):
                pmax = int(v)

        info[self.MAX] = pmax
        info[self.MIN] = pmin

    def getPageElem(self):
        pageret = { self.ENABLE : self.FALSE }
        self.parsePageNum(pageret)
        if self.MIN in pageret \
            and self.MAX in pageret \
            and pageret[self.MIN] != pageret[self.MAX]:
            pageret[self.ENABLE] = self.TRUE
        self.addMorePage(pageret)
        return pageret

    def addMorePage(self, info):
        disable = r'span.pagination__next'
        diso = self.soup.select_one(disable)
        if diso:
            return
        next = r'a.pagination__next'
        nexto = self.soup.select_one(next)
        if not nexto:
            return
        info[self.MOREPAGE] = self.TRUE
        return