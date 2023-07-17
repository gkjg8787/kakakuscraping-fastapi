import re
from bs4 import BeautifulSoup
from html_parser.search_parser import SearchParser

class SearchNetoff(SearchParser):

        
    def parseSearch(self, htmltext):
        self.soup = BeautifulSoup(htmltext,"html.parser")
        self.allitem[self.ITEMS] = self.parseItems()
        self.allitem[self.PAGE] = self.getPageElem()
    
    def parseItems(self):
        q = r'#resultList .resultRow'
        ret = self.soup.select(q)
        sresult = []
        for v in ret:
            itemd ={}
            itemd[self.STORENAME] = "ネットオフ"
            itemd[self.IMAGE_ON_ERR] = "https://st.netoff.co.jp/ebimage/noimage_comic_01.gif"
            self.setTitle(v, itemd)
            self.setImage(v, itemd)
            self.setCategory(v, itemd)
            self.setPrice(v, itemd)
            self.setMailBin(v, itemd)
            self.setSubInfo(v, itemd)
            sresult.append(itemd)
        return sresult



    def allprint(self, htmltext):
        self.parseSearch(htmltext)
        print(self.allitem)

    def setCategory(self, elem, itemd):
        cateo = elem.select('.catList')
        itemd[self.CATEGORY] = cateo[0].text

    def setImage(self, elem, itemd):
        imageo = elem.select('.showimage img')
        if len(imageo) == 0:
            self.createImageURL(elem, itemd)
            return

        itemd[self.IMAGE_URL] = imageo[0]['src']
    
    def createImageURL(self, elem, itemd):
        imageo = elem.select('.rowList span')
        ptn = r'span class="([0-9]+)"'
        for e in imageo:
            m = re.findall(ptn, str(e))
            if m == None or len(m) == 0: continue
            itemd[self.IMAGE_URL] = 'https://www.netoff.co.jp/ebimage/cmdty/' + str(m[0]) + '.jpg'
            return

    def setTitle(self, elem, itemd):
        titleo = elem.select('.titleBox a')
        itemd[self.TITLE] = titleo[0].text
        itemd[self.TITLE_URL] = self.getPerfectURL(titleo[0]['href'])

    def getPerfectURL(self, url):
        ptn = r'^/'
        m = re.findall(ptn, url)
        if m == None or len(m) == 0: return url
        return 'https://www.netoff.co.jp' + url

    def setPrice(self, elem, itemd):
        self.setStockPrice(elem, itemd)
        if not self.PRICE in itemd:
            self.setSinagire(elem, itemd)
        else:
            self.setZaiko(elem, itemd)

    def setStockPrice(self, elem, itemd):
        stocko = elem.select('.priceTrue')
        if len(stocko) == 0:
            return
        text = self.matchPrice(stocko[0].text)
        itemd[self.PRICE] = text

    def setSinagire(self, elem, itemd):
        stocko = elem.select('.priceFalse')
        if len(stocko) == 0:
            return
        text = self.matchPrice(stocko[0].text)
        itemd[self.PRICE] = text
        itemd[self.SINAGIRE] = '品切れ'

    def matchPrice(self, basetext):
        ptn = r'[1-9][0-9,]+円'
        text = self.htmlTrim(basetext)
        text = re.findall(ptn, text)
        return text[0]
    
    def setZaiko(self, elem, itemd):
        zaikoo = elem.select('.stock_lastone')
        if len(zaikoo) == 0:
            return
        itemd[self.ZAIKO] = zaikoo[0].text

    def setMailBin(self, elem, itemd):
        mailo = elem.select('.j3')
        if len(mailo) == 0:
            return
        itemd[self.MAILBIN] = mailo[0].text

    def setSubInfo(self, elem, itemd):
        subinfoo = elem.select('.subinfo')
        if len(subinfoo) == 0:
            return
        itemd[self.SUBINFO] = subinfoo[0].text
        
    def addPageNum(self, elems, val):
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

    def getPageElem(self):
        q = r'.pager ol li'
        pages = self.soup.select(q)
        if pages is None : return "None"
        pageret = { self.ENABLE : self.FALSE }
        for p in pages:
            #print(p.text)
            self.addPageNum(pageret, p.text)
            if self.MIN in pageret \
                and self.MAX in pageret\
                and pageret[self.MIN] != pageret[self.MAX]:
                pageret[self.ENABLE] = self.TRUE
        self.addMorePage(pageret)
        return pageret

    def addMorePage(self, info):
        q = r'.pager .rightBtn'
        moreo = self.soup.select(q)
        if len(moreo) != 0:
            info[self.MOREPAGE] = self.TRUE
