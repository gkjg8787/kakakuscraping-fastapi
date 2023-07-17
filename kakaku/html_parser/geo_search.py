import re
from bs4 import BeautifulSoup
from html_parser.search_parser import SearchParser


class SearchGeo(SearchParser):

        
    def parseSearch(self, htmltext):
        self.soup = BeautifulSoup(htmltext,"html.parser")
        self.allitem[self.ITEMS] = self.parseItems()
        self.allitem[self.PAGE] = self.getPageElem()
    
    def parseItems(self):
        q = r'ul.itemList li'
        ret = self.soup.select(q)
        sresult = []
        for v in ret:
            itemd ={}
            itemd[self.STORENAME] = "ゲオ"
            itemd[self.IMAGE_ON_ERR] = "https://ec.geo-online.co.jp/img/sys/sorryL.jpg"
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
        titleo = elem.select('.itemName')
        itemd[self.TITLE] = titleo[0].text.replace('\u3000', ' ')
        titleurlo = elem.select('a.sendDatalayer')
        itemd[self.TITLE_URL] = self.getPerfectURL(titleurlo[0]['href'])

    def getPerfectURL(self, url):
        ptn = r'^/'
        m = re.findall(ptn, url)
        if m == None or len(m) == 0: return url
        return 'https://ec.geo-online.co.jp' + url

    def setCategory(self, elem, itemd):
        cateo = elem.select('.itemCarrier')
        itemd[self.CATEGORY] = cateo[0].text.replace('\u3000', ' ')

    def setImage(self, elem, itemd):
        imageo = elem.select('.itemImage img')
        if len(imageo) == 0:
            self.createImageURL(elem, itemd)
            return

        itemd[self.IMAGE_URL] = imageo[0]['src']
    
    def createImageURL(self, elem, itemd):
        itemd[self.IMAGE_URL] = 'https://ec.geo-online.co.jp/img/sys/sorryL.jpg'


    def setPrice(self, elem, itemd):
        price = self.getMainPrice(elem)
        istate = self.getItemState(elem, itemd)
        if '新品' in istate:
            itemd[self.NEW] = price
        else:
            itemd[self.USED] = price


    def getMainPrice(self, elem):
        q = r'.sellPtnLeftPrice'
        priceo = elem.select(q)
        pricetext = self.htmlTrim(priceo[0].text)
        return pricetext
    
    def getItemState(self, elem, itemd):
        q = r'.labelSituation'
        tro = elem.select(q)
        ret = ''
        for tr in tro:
            if '予約' in tr.text:
                itemd[self.YOYAKU] = tr.text
                continue
            if ret == '':
                ret = tr.text
                itemd[self.STATE] = tr.text
                
        return ret

        
    def parsePageNum(self, info):
        q = r'.pager li'
        pages = self.soup.select(q)
        if len(pages) == 0: return
        text = str(pages)
        ptn = r'>([0-9]+)<'
        m = re.findall(ptn, text)
        #print('text={} , m={}'.format(text, m))
        pmin = -1
        pmax = -1
        for v in m:
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
        q = r'.pager li.next'
        moreo = self.soup.select(q)
        if len(moreo) == 0 : return
        nmo = moreo[0].get('class')
        if 'noMove' in nmo: return
        info[self.MOREPAGE] = self.TRUE