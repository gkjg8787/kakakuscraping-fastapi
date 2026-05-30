import re

from bs4 import BeautifulSoup

from html_parser import htmlparse
from itemcomb import postage_data as posd

DEFAULT_STORENAME = "ブックオフ"


class BookoffParse(htmlparse.ParseItems):
    def __init__(self, fp, id, date, url):
        self.soup = BeautifulSoup(fp, "html.parser")
        self.iteminfo = htmlparse.ParseItemInfo()
        self.iteminfo.id = id
        self.iteminfo.timeStamp = date
        self.iteminfo.url = url
        self.iteminfo.storename = DEFAULT_STORENAME
        self.parseItem(self.soup, self.iteminfo)

    def parseItem(self, soup, iteminfo):
        iteminfo.isSuccess = True
        iteminfo.name = self.parseTitle(soup)
        if not self.existZaiko(soup):
            iteminfo.isSuccess = False
            return
        self.parsePrice(soup, iteminfo)

    def existZaiko(self, soup):
        q = r".productInformation__stock__alert"
        elem = soup.select(q)
        if len(elem) != 0:
            return True
        return False

    def parseTitle(self, soup):
        q = r".productInformation__title"
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
        q = r".productInformation__price--large"
        elem = soup.select(q)
        ptn = r"([1-9][0-9,]+)"
        for e in elem:
            m = re.findall(ptn, e.text)
            if len(m) == 0:
                continue
            return int(m[0].replace(",", ""))
        return None

    def parseUsedPrice(self, soup, iteminfo, price):
        if not price:
            return False
        q = r".productInformation__Btn__used.-active"
        elem = soup.select_one(q)
        if elem:
            iteminfo.usedPrice = int(price)
            return True
        return False

    def parseNewPrice(self, soup, iteminfo, price):
        if not price:
            return False
        q = r".productInformation__Btn__new.-active"
        elem = soup.select_one(q)
        if elem:
            iteminfo.newPrice = int(price)
            return True
        return False

    def getTaxin(self, elem):
        return True

    def getItems(self):
        return (self.iteminfo,)


class BookoffAnswerParse:

    def __init__(self, fp):
        self.soup = BeautifulSoup(fp, "html.parser")

    def get_ParseStorePostage(self) -> list[htmlparse.ParseStorePostage]:
        # 元の命名規則（大文字開始）を維持し、内部で解析メソッドを呼び出す
        return self._parse_page(self.soup)

    def _parse_page(self, soup: BeautifulSoup) -> list[htmlparse.ParseStorePostage]:
        results: list[htmlparse.ParseStorePostage] = []

        # ユニークな「faq-layout-container」から、回答本文が含まれる「div.md p」をすべて取得
        container = soup.select_one(".faq-layout-container")
        if not container:
            return results

        p_list = container.select("div.md p")

        for p in p_list:
            # 空白や改行を排除
            target_text = re.sub(r"\s+", "", p.text)
            if not target_text:
                continue

            # 送料無料パターンの解析
            free_psp = self._parse_free_shipping(target_text)
            if free_psp:
                results.append(free_psp)
                continue

            # 全国一律料金パターンの解析
            cw_psp = self._parse_country_wide_flat_rate(target_text)
            if cw_psp:
                results.append(cw_psp)
                continue

        return results

    def _parse_free_shipping(self, target_text: str):
        # 「税込み1,800円以上」の「税込」や「税込み」表記があっても無視できるよう正規表現を調整
        # 例: "税込み1,800円以上の注文で送料無料です"
        m = re.findall(
            r"([1-9][0-9]+)円(以上)の注文で送料(無料)",
            target_text.replace(",", ""),
        )
        if not m:
            return None
        if not m[0][0] or not m[0][1] or not m[0][2]:
            return None

        psp = self._create_parsestorepostage(
            boundary_ope="<=", boundary_val=int(m[0][0]), postage=0
        )
        return psp

    def _parse_country_wide_flat_rate(self, target_text: str):
        # 新HTMLの「全国一律で368円」に対応（「日本」が無くてもマッチするように修正）
        # 例: "税込み1,800円未満の場合、全国一律で368円です"
        m = re.findall(
            r"([1-9][0-9]+)円(未満)の場合、(?:日本)?全国一律で?([1-9][0-9]+)円",
            target_text.replace(",", ""),
        )
        if not m:
            return None
        if not m[0][0] or not m[0][1] or not m[0][2]:
            return None

        psp = self._create_parsestorepostage(
            boundary_ope=">", boundary_val=int(m[0][0]), postage=int(m[0][2])
        )
        return psp

    def _create_parsestorepostage(
        self, boundary_ope: str, boundary_val: int, postage: int
    ):
        psp = htmlparse.ParseStorePostage()
        psp.storename = DEFAULT_STORENAME
        ppt = htmlparse.ParsePostageTerms()
        ppt.boundary = posd.ShippingTermsBoundary.create_boundary_of_db(
            lower_ope=boundary_ope, lower_val=boundary_val
        )
        ppt.postage = postage
        psp.add_terms(ppt)
        return psp
