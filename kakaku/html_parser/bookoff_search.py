
import re
from bs4 import BeautifulSoup
from html_parser.search_parser import SearchParser


class SearchBookoff(SearchParser):

        
    def parseSearch(self, htmltext):
        self.soup = BeautifulSoup(htmltext,"html.parser")
        self.allitem[self.ITEMS] = self.parseItems()
        self.allitem[self.PAGE] = self.getPageElem()
    
    def parseItems(self):
        q = r'#resList .list_group'
        ret = self.soup.select(q)
        sresult = []
        for v in ret:
            itemd ={}
            itemd[self.STORENAME] = "ブックオフ"
            itemd[self.IMAGE_ON_ERR] = "https://content.bookoffonline.co.jp/images/goods/item_l.gif"
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
        titleo = elem.select('.itemttl a')
        itemd[self.TITLE] = titleo[0].text
        itemd[self.TITLE_URL] = self.getPerfectURL(titleo[0]['href'])

    def getPerfectURL(self, url):
        ptn = r'^/'
        m = re.findall(ptn, url)
        if m == None or len(m) == 0: return url
        return 'https://www.bookoffonline.co.jp' + url

    def setCategory(self, elem, itemd):
        cateo = elem.select('.subtitle')
        itemd[self.CATEGORY] = cateo[0].text.replace('\u3000', ' ')

    def setImage(self, elem, itemd):
        imageo = elem.select('.list_l img')
        if len(imageo) == 0:
            self.createImageURL(elem, itemd)
            return

        itemd[self.IMAGE_URL] = imageo[0]['src']
    
    def createImageURL(self, elem, itemd):
        itemd[self.IMAGE_URL] = 'https://content.bookoffonline.co.jp/images/goods/item_l.gif'

    def setPrice(self, elem, itemd):
        price = self.getMainPrice(elem)
        isnew = self.isNewPrice(elem)
        if isnew:
            itemd[self.NEW] = price
        else:
            itemd[self.USED] = price

        self.setSinagire(elem, itemd)

    def getMainPrice(self, elem):
        q = r'.mainprice'
        priceo = elem.select(q)
        ptn = r'(￥[1-9][0-9,]+（税込）)'
        m = re.findall(ptn, self.htmlTrim(priceo[0].text))
        return m[0]
    
    def isNewPrice(self, elem):
        q = r'.details tr'
        tro = elem.select(q)
        tabq = r'th.tab01'
        for tr in tro:
            tabo = tr.select(tabq)
            if len(tabo) == 0:
                continue
            if '中古価格' in tabo[0].text:
                return False
        return True

    def setSinagire(self, elem, itemd):
        stocko = elem.select('.nostockbtn')
        if len(stocko) != 0:
            itemd[self.SINAGIRE] = '品切れ'
        
    def parsePageNum(self, info):
        q = r'.numNavi'
        pages = self.soup.select(q)
        if len(pages) == 0: return
        text = self.htmlTrim(pages[0].text)
        ptn = r'\[([0-9]+)\]'
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
        q = r'.numNavi a'
        moreo = self.soup.select(q)
        for p in moreo:
            if '次へ' in p.text:
                info[self.MOREPAGE] = self.TRUE
                return