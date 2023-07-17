import re
from bs4 import BeautifulSoup
from html_parser.search_parser import SearchParser

class SearchSurugaya(SearchParser):        


    def parseSearch(self, htmltext):
        self.soup = BeautifulSoup(htmltext,"html.parser")
        self.allitem[self.ITEMS] = self.parseItems()
        self.allitem[self.PAGE] = self.getPageElem()
    
    def parseItems(self):
        q = r' .item_box .item'
        ret = self.soup.select(q)
        sresult = []
        for v in ret:
            itemd ={}
            itemd[self.STORENAME] = "駿河屋"
            self.setTitle(v, itemd)
            self.setCategory(v, itemd)
            self.setPrice(v, itemd)
            self.setImage(v, itemd)
            sresult.append(itemd)
        return sresult


    def allprint(self, htmltext):
        self.parseSearch(htmltext)
        print(self.allitem)

    def setCategory(self, elem, itemd):
        conditiono = elem.select('.condition')
        ptn = r'([^\s]+)\s*?|'
        text = self.trimStr(conditiono[0].text)
        m = re.findall(ptn, text)
        itemd[self.CATEGORY] = m[0]
    
    def setImage(self, elem, itemd):
        imageo = elem.select('.photo_box img')
        itemd[self.IMAGE_URL] = imageo[0]['src']

    def setTitle(self, elem, itemd):
        titleo = elem.select('.title a')
        #print(titleo[0].text)
        itemd[self.TITLE] = titleo[0].text
        itemd[self.TITLE_URL] = self.getPerfectURL(titleo[0]['href'])

    def getPerfectURL(self,url):
        ptn = r'^/product'
        m = re.findall(ptn, url)
        if m == None or len(m) == 0: return url
        return 'https://www.suruga-ya.jp' + url


    def setPrice(self, elem, itemd):
        priceo = elem.select('.item_price')
        #print(priceo)
        def in_sinagire(priceo, itemd):
            sinagire = priceo.select('.price')
            #print('sinagire len='+str(len(sinagire)))
            if len(sinagire) == 0: return
            itemd[self.SINAGIRE] = self.htmlTrim(sinagire[0].text)
        
        self.setErrorThrough(in_sinagire, priceo[0], itemd)

        def in_teika(priceo, itemd):
            teika = priceo.select('.price_teika')
            for v in teika:
                if '中古' in v.text:
                    itemd[self.USED] = self.htmlTrim(v.text)
                    #print('used='+ v.text)
                    continue
                if '新品' in v.text:
                    itemd[self.NEW] = self.htmlTrim(v.text)
                    #print('new='+ v.text)
                    continue
                if '定価' in v.text:
                    continue
                if '￥' in v.text:
                    if not self.USED in itemd:
                        itemd[self.USED] = self.htmlTrim(v.text)

        self.setErrorThrough(in_teika, priceo[0], itemd)
        
        def in_makepure(priceo, itemd):
            makepure = priceo.select('.mgnB5')
            if len(makepure) == 0 : return
            #print('makepure='+makepure[0].text)
            itemd[self.MAKEPURE] = self.htmlTrim(makepure[0].text)

            makepureopt = priceo.select('.mgnL-3 a')
            if len(makepureopt) == 0 : return
            itemd[self.MAKEPURE_BIKO] = self.htmlTrim(makepureopt[0].text)
            itemd[self.MAKEPURE_URL] = self.getPerfectURL(makepureopt[0]['href'])
        
        self.setErrorThrough(in_makepure, priceo[0], itemd)

    def setErrorThrough(self, func, elem, itemd):
        try:
            func(elem, itemd)
        except AttributeError:
            pass
        
    def getPageElem(self):
        q = 'div#pager'
        pages = self.soup.select(q)
        if pages is None : return
        pageret = { self.ENABLE: self.FALSE }
        for p in pages:
            pls = p.select('li')
            for pl in pls:
                self.addPageNum(pageret, pl.text)
                if self.MIN in pageret : pageret[self.ENABLE] = self.TRUE
            pu = p.select('ul')
            for u in pu:
                self.addMorePage(pageret, u.text)

        return(pageret)

    def addPageNum(self, elems, val):
        if '...' in val:
            val.translate(str.maketrans({' ':None, '...': None }))
        if str.isdigit(val):
            num = int(val)
            if self.MIN in elems :
                if elems[self.MIN] > num : elems[self.MIN] = num
            else:
                elems[self.MIN] = num

            if self.MAX in elems:
                if elems[self.MAX] < num : elems[self.MAX] = num
            else:
                elems[self.MAX] = num

    def addMorePage(self, elems, val):
        if '...' in val:
            elems[self.MOREPAGE] = self.TRUE
