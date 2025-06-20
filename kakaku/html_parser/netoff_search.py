import re
from bs4 import BeautifulSoup
from html_parser.search_parser import SearchParser


class SearchNetoff(SearchParser):
    def parseSearch(self, htmltext):
        self.soup = BeautifulSoup(htmltext, "html.parser")
        self.allitem[self.ITEMS] = self.parseItems()
        self.allitem[self.PAGE] = self.getPageElem()

    def parseItems(self):
        q = r"li.l-search__products"
        ret = self.soup.select(q)
        sresult = []
        for v in ret:
            itemd = {}
            itemd[self.STORENAME] = "ネットオフ"
            itemd[self.IMAGE_ON_ERR] = (
                "https://st.netoff.co.jp/ebimage/noimage_comic_01.gif"
            )
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
        cateo = elem.select_one(".c-cassette__label")
        itemd[self.CATEGORY] = cateo.text

    def setImage(self, elem, itemd):
        imageo = elem.select_one(r"a.c-cassette__img img")
        fname = re.sub(r"\D", "", str(imageo["src"])) + ".jpg"
        itemd[self.IMAGE_URL] = "https://www.netoff.co.jp/ebimage/cmdty/" + fname

    def setTitle(self, elem, itemd):
        titleo = elem.select_one(r"a.c-cassette__title")
        itemd[self.TITLE] = titleo.text
        itemd[self.TITLE_URL] = self.getPerfectURL(titleo["href"])

    def getPerfectURL(self, url):
        ptn = r"^/"
        m = re.findall(ptn, url)
        if m is None or len(m) == 0:
            return url
        return "https://www.netoff.co.jp" + url

    def setPrice(self, elem, itemd):
        self.setStockPrice(elem, itemd)
        if self.is_sinagire(elem):
            itemd[self.SINAGIRE] = "品切れ"
        else:
            zaikoo = elem.select_one(r".c-cassette__stock--message")
            if zaikoo:
                itemd[self.ZAIKO] = zaikoo.text

    def setStockPrice(self, elem, itemd):
        stocko = elem.select(".c-cassette__price")
        if len(stocko) == 0:
            return
        text = self.matchPrice(stocko[0].text)
        itemd[self.PRICE] = text

    def is_sinagire(self, elem):
        ret = elem.select_one(r".c-button--mail--outline")
        if ret:
            return True
        return False

    def matchPrice(self, basetext):
        ptn = r"[1-9][0-9,]+円"
        text = self.htmlTrim(basetext)
        text = re.findall(ptn, text)
        return text[0]

    def setMailBin(self, elem, itemd):
        mailo = elem.select(".c-cassette__label")
        if len(mailo) == 0:
            return
        for m in mailo:
            if "メール便" in m.text:
                itemd[self.MAILBIN] = m.text
                return
            else:
                continue

    def setSubInfo(self, elem, itemd):
        subinfoo = elem.select(".c-cassette__author")
        if len(subinfoo) == 0:
            return
        itemd[self.SUBINFO] = subinfoo[0].text

    def addPageNum(self, elems, val):
        if str.isdigit(val):
            num = int(val)
            if self.MIN in elems:
                if elems[self.MIN] > num:
                    elems[self.MIN] = num
            else:
                elems[self.MIN] = num

            if self.MAX in elems:
                if elems[self.MAX] < num:
                    elems[self.MAX] = num
            else:
                elems[self.MAX] = num

    def getPageElem(self):
        q = r".c-pagination li"
        pages = self.soup.select(q)
        if pages is None:
            return "None"
        pageret = {self.ENABLE: self.FALSE}
        for p in pages:
            # print(p.text)
            self.addPageNum(pageret, p.text)
            if (
                self.MIN in pageret
                and self.MAX in pageret
                and pageret[self.MIN] != pageret[self.MAX]
            ):
                pageret[self.ENABLE] = self.TRUE
        self.addMorePage(pageret)
        return pageret

    def addMorePage(self, info):
        q = r".c-pagination .c-pagination_next"
        moreo = self.soup.select(q)
        if len(moreo) != 0:
            info[self.MOREPAGE] = self.TRUE
