import re
from html_parser import htmlparse
from bs4 import BeautifulSoup, Tag
from abc import ABCMeta
from datetime import datetime

from itemcomb import postage_data

DEFAULT_STORENAME = "駿河屋"


class AB_SurugayaParse(htmlparse.ParseItems, metaclass=ABCMeta):
    @classmethod
    def checkSuccess(cls, itemInfo: htmlparse.ParseItemInfo):
        np = int(itemInfo.newPrice)
        up = int(itemInfo.usedPrice)
        if np <= 0 and up <= 0:
            return False
        else:
            return True


class SurugayaProduct_Other(AB_SurugayaParse):
    soup: BeautifulSoup
    iteminfos: tuple[htmlparse.ParseItemInfo]

    def __init__(self, soup: BeautifulSoup, id: int, date: datetime, url: str):
        self.soup = soup
        self.iteminfos = []
        title = self.getTitle(self.soup)
        baseinfo = {
            "storename": DEFAULT_STORENAME,
            "id": id,
            "title": title,
            "date": date,
            "url": url,
        }
        self.iteminfos = tuple(self.parseStoreItem(self.soup, baseinfo))

    def getItems(self):
        return self.iteminfos

    @classmethod
    def createParseItemInfo(
        cls, storename: str, id: int, title: str, date: datetime, url: str
    ):
        item = htmlparse.ParseItemInfo()
        item.storename = storename
        item.id = id
        item.name = title
        item.timeStamp = date
        item.url = url
        return item

    @classmethod
    def getTitle(cls, soup: BeautifulSoup):
        titlebody = "h1.title_product.mgnB15"
        retstr = soup.select_one(titlebody)
        if not retstr:
            return ""
        namestr = cls.trimStr(retstr.text).replace("の取り扱い店舗一覧", "")
        return namestr

    @classmethod
    def createSinagire(cls, binfo: dict):
        return [
            cls.createParseItemInfo(
                storename=binfo["storename"],
                id=binfo["id"],
                title=binfo["title"],
                date=binfo["date"],
                url=binfo["url"],
            )
        ]

    @classmethod
    def parseStoreItem(cls, soup: BeautifulSoup, binfo: dict):
        retitems = []
        tableq = r"table#tbl_all .item"
        storeitems = soup.select(tableq)
        if len(storeitems) == 0:
            return cls.createSinagire(binfo)

        for storeitem in storeitems:
            item = cls.createParseItemInfo(
                binfo["storename"],
                binfo["id"],
                binfo["title"],
                binfo["date"],
                binfo["url"],
            )
            price = cls.getPrice(storeitem)
            isNew = cls.isNewItem(storeitem)
            storename = cls.getStoreName(storeitem)
            if isNew:
                item.newPrice = price
            else:
                item.usedPrice = price
            if storename:
                item.storename = storename
            item.onSale = False
            if item.storename == DEFAULT_STORENAME:
                item.saleName = cls.getSaleName(storeitem)
                if item.saleName:
                    item.onSale = True
            item.taxin = True
            item.isSuccess = cls.checkSuccess(item)
            retitems.append(item)
        return retitems

    @classmethod
    def getPrice(cls, storeitem: Tag):
        pattern = r'<strong class="text-red text-bold mgnL10.+?>(.*?)円'
        m = re.findall(pattern, str(storeitem))
        # print("------------isTblPrice-----------")
        # print(m)
        price = str(m[0]).replace(",", "")
        price = int(re.sub("\\D", "", price))
        return price

    @classmethod
    def isNewItem(cls, storeitem: Tag):
        pattern = r'<h2 class="title_product">(.+?)</h2>'
        # print(text)
        m = re.findall(pattern, str(storeitem))
        # print("------------isTblNewUsed-----------")
        # print(m)
        statusstr = cls.trimStr(str(m[0]))
        if "新品" in statusstr:
            return True
        return False

    @classmethod
    def getStoreName(cls, storeitem: Tag):
        q = r"div.space_text_1.mgnB5 a"
        elem = storeitem.select(q)
        if len(elem) == 0:
            return ""
        return re.sub(r"\s+", " ", str(elem[0].text).strip())

    @classmethod
    def getSaleName(cls, storeitem: Tag) -> str:
        pattern = r'<strong class="mgnL10 text-line-through.+?>(.*?)円'
        m = re.findall(pattern, str(storeitem))
        if not m:
            return ""
        price = str(m[0]).replace(",", "")
        price = int(re.sub("\\D", "", price))
        if price == 0:
            return ""
        return "タイムセール"


class SurugayaProduct(AB_SurugayaParse):
    soup: BeautifulSoup
    iteminfo: htmlparse.ParseItemInfo

    def __init__(self, soup: BeautifulSoup, id: int, date: datetime, url: str):
        self.soup = soup
        self.iteminfo = htmlparse.ParseItemInfo()
        self.iteminfo.id = id
        self.iteminfo.timeStamp = date
        self.iteminfo.url = url
        self.iteminfo.name = self.parseTitle(self.soup)
        self.set_parsePrice(self.soup, self.iteminfo)
        self.set_isSale(self.soup, self.iteminfo)
        self.iteminfo.isSuccess = self.checkSuccess(self.iteminfo)
        self.iteminfo.storename = self.getStoreName(self.soup)

    def getItems(self):
        return (self.iteminfo,)

    @classmethod
    def parseTitle(cls, soup: BeautifulSoup):
        titlebody = "#item_title"
        retstr = soup.select_one(titlebody)
        namestr = cls.trimStr(retstr.text)
        # print("title:"+namestr)
        return namestr

    def parseTaxin(self, text: str, iteminfo: htmlparse.ParseItemInfo):
        if iteminfo.taxin:
            return
        if "税込み" in str(text) or "税込" in str(text):
            iteminfo.taxin = True

    def set_parsePrice(self, soup: BeautifulSoup, iteminfo: htmlparse.ParseItemInfo):
        basebody = r"label.mgnB0.d-block"
        datal = soup.select(basebody)
        isNew = False
        pattern = '<span.+?buy">(.+?)</span>'
        for val in datal:
            # print(val.text)
            if "新品" in val.text:
                isNew = True
            elif "中古" in val.text:
                isNew = False

            ret = re.findall(pattern, str(val))
            retlen = len(ret)
            if retlen == 0:
                continue
            self.parseTaxin(val.text, iteminfo)
            if isNew:
                # print("newPrice:"+str(val.text))
                iteminfo.newPrice = int(re.sub("\\D", "", str(ret[0])))
            else:
                # print("usedPrice:"+str(val.text))
                iteminfo.usedPrice = int(re.sub("\\D", "", str(ret[0])))

    def set_isSale(self, soup: BeautifulSoup, iteminfo: htmlparse.ParseItemInfo):
        timesalebase = soup.select_one(
            "div.container_suru.padB40 > .row > .col-8.padL32 .flash_sale_title"
        )
        if timesalebase is not None:
            # print("Sale:"+str(timesalebase.text))
            iteminfo.onSale = True
            iteminfo.saleName = self.trimStr(timesalebase.text)
        else:
            iteminfo.onSale = False

    def getOrderedDict(self):
        return self.iteminfo.getOrderedDict()

    def getTrendRate(self):
        return self.iteminfo.getTrendRate()

    def getName(self):
        return self.iteminfo.name

    @classmethod
    def getStoreName(cls, soup: BeautifulSoup) -> str:
        tags = soup.select(".mb-2")
        ptn = r"この商品は、(.*)が販売、発送します"
        storename = None
        if not tags:
            return DEFAULT_STORENAME
        for tag in tags:
            m = re.findall(ptn, str(tag.text))
            if m is None or len(m) == 0:
                continue
            storename = cls.trimStr(m[0])
            if storename:
                return storename
        return DEFAULT_STORENAME


def is_makepure(soup: BeautifulSoup):
    ret = SurugayaProduct_Other.getTitle(soup)
    if ret:
        return True
    return False


class SurugayaMakepurePostage:
    parseStorePostageList: list[htmlparse.ParseStorePostage] = []
    shopid_dict: dict[str, htmlparse.ParseShopIDInfo] = {}

    def __init__(self, soup: BeautifulSoup):
        if not is_makepure(soup):
            if DEFAULT_STORENAME == SurugayaProduct.getStoreName(soup):
                return
            self.parse_html_for_detail(soup=soup)
            return
        self.parse_html_for_other(soup=soup)

    def get_ParseStorePostage(self):
        return self.parseStorePostageList

    def get_ParseShopIDInfo(self):
        return self.shopid_dict

    @classmethod
    def parse_storename(cls, elem: Tag):
        storeret = elem.select_one(r".space_text_1")
        if storeret:
            t = str(storeret.text).strip()
            tt = re.sub(r"\s+", " ", t)
            return tt
        else:
            return DEFAULT_STORENAME

    def parse_html_for_other(self, soup: BeautifulSoup):
        storepos_results: dict[str, htmlparse.ParseStorePostage] = {}
        sidinf_results: dict[str, htmlparse.ParseShopIDInfo] = {}
        store_row = soup.select(r"#tabs-all tr.item")
        for row in store_row:
            storename = self.parse_storename(row)
            storepos = self.parse_storepostage(
                row, storename=storename, storepos_results=storepos_results
            )
            if storepos:
                storepos_results[storepos.storename] = storepos

            sidinf = self.parse_shopidinfo(
                row, storename=storename, sidinf_results=sidinf_results
            )
            if sidinf:
                sidinf_results[sidinf.storename] = sidinf

        self.parseStorePostageList = [v for v in storepos_results.values()]
        self.shopid_dict = sidinf_results

    @classmethod
    def parse_shopidinfo(
        cls,
        elem: Tag,
        storename: str,
        sidinf_results: dict[str, htmlparse.ParseShopIDInfo],
    ):
        if DEFAULT_STORENAME == storename:
            return None
        if storename in sidinf_results:
            return None
        sidinf = htmlparse.ParseShopIDInfo()
        sidinf.storename = storename

        storeret = elem.select_one(r".space_text_1 a")
        if not storeret:
            return None
        sidinf.url = "https://www.suruga-ya.jp" + storeret["href"]
        m = re.findall(r"[1-9][0-9]+", storeret["href"])
        if not m:
            return None
        sidinf.shop_id = int(m[0])
        return sidinf

    @classmethod
    def parse_storepostage(
        cls,
        elem: Tag,
        storename: str,
        storepos_results: dict[str, htmlparse.ParseStorePostage],
    ):
        if storename in storepos_results:
            return None
        StorePostage = htmlparse.ParseStorePostage()
        StorePostage.storename = storename

        pos_list = elem.select(r".padT5")
        for pos in pos_list:
            if "発送します" in pos.text:
                continue
            if "返品について" in pos.text:
                continue

            t = str(pos.text).strip()
            tt = re.sub(r"\s+", " ", t)
            StorePostage.campaign_msg = tt

            pr = pos.select(r".padR5")
            pl = pos.select(r".padL5")
            if len(pr) != len(pl):
                continue
            pre_terms: htmlparse.ParsePostageTerms | None = None
            for prr, pll in zip(pr, pl):
                terms = cls.create_terms(
                    boundary_text=prr.text.strip(),
                    postage_text=pll.text.strip(),
                    pre_terms=pre_terms,
                )
                if terms:
                    StorePostage.add_terms(terms)
                    pre_terms = terms
                    continue
        return StorePostage

    @classmethod
    def create_terms(
        cls,
        boundary_text: str,
        postage_text: str,
        pre_terms: htmlparse.ParsePostageTerms | None,
    ):
        boundary = cls.create_boundary(boundary_text=boundary_text, pre_terms=pre_terms)
        if not boundary:
            return None
        postage = cls.create_postage(postage_text=postage_text)
        if postage < 0:
            return None
        terms = htmlparse.ParsePostageTerms()
        terms.boundary = boundary
        terms.postage = postage
        return terms

    @classmethod
    def create_postage(
        cls,
        postage_text: str,
    ) -> int:
        if "送料無料" in postage_text:
            return 0
        p_text = postage_text.replace(",", "")
        range_ptn = r"[0-9]+～[1-9][0-9]+円"
        m = re.findall(range_ptn, p_text)
        if m:
            return -1
        ptn = r"([1-9][0-9]+)円"
        m = re.findall(ptn, p_text)
        if not m:
            return -1
        return int(m[0])

    @classmethod
    def create_boundary(
        cls, boundary_text: str, pre_terms: htmlparse.ParsePostageTerms | None
    ):
        b_ptn = r"([1-9][0-9]+)円(以上|未満)"
        m = re.findall(b_ptn, boundary_text.replace(",", ""))
        if not m:
            return None
        boundary_val = m[0][0]
        boundary_ope = ""
        if m[0][1] == "以上":
            boundary_ope = "<="
        if m[0][1] == "未満":
            boundary_ope = ">"
        boundary = f"{boundary_val}{boundary_ope}"
        if pre_terms:
            bval, bope = cls.get_pre_val_and_operator_in_text(pre_terms.boundary)
            if not bval or not bope:
                return boundary
            if not cls.is_compounding_terms(
                cur_boundary_ope=boundary_ope,
                cur_boundary_val=int(boundary_val),
                pre_boundary_ope=bope,
                pre_boundary_val=int(bval),
            ):
                return boundary
            rev_ope = postage_data.ShippingTermsBoundary.reverse_operator(bope)
            boundary = f"{bval}{rev_ope}:{boundary}"
        return boundary

    @staticmethod
    def is_compounding_terms(
        cur_boundary_ope: str,
        cur_boundary_val: int,
        pre_boundary_ope: str,
        pre_boundary_val: int,
    ):
        return (
            pre_boundary_ope == ">"
            and cur_boundary_ope == ">"
            and pre_boundary_val < cur_boundary_val
        )

    @staticmethod
    def get_pre_val_and_operator_in_text(boundary_text: str):
        rets = (
            postage_data.ShippingTermsBoundary.get_list_of_boundary_value_and_operation(
                boundary_text=boundary_text
            )
        )
        boundary_ope = None
        boundary_val = None
        if len(rets) == 2:
            boundary_val = rets[1]["boundary_val"]
            boundary_ope = rets[1]["boundary_ope"]
        elif len(rets) == 1:
            boundary_val = rets[0]["boundary_val"]
            boundary_ope = rets[0]["boundary_ope"]
        return boundary_val, boundary_ope

    @classmethod
    def get_boundary_text(cls, text: str):
        ret = text
        ret = ret.replace(" ", "")
        ret = ret.replace(",", "")
        return ret

    def parse_html_for_detail(self, soup: BeautifulSoup):
        sidinf_results: dict[str, htmlparse.ParseShopIDInfo] = {}
        sidinf_results = self.parse_shopidinfo_for_detail(soup=soup)
        self.shopid_dict = sidinf_results

        pss = htmlparse.ParseStorePostage()
        if not sidinf_results:
            return
        pss.storename = [k for k in sidinf_results.keys()][0]
        self.parseStorePostageList = [pss]

    @classmethod
    def parse_shopidinfo_for_detail(
        cls, soup: BeautifulSoup
    ) -> dict[str, htmlparse.ParseItemInfo]:
        sidinf = htmlparse.ParseShopIDInfo()

        tags = soup.select(".mb-2")
        ptn = r"この商品は、(.*)が販売、発送します"
        storename = None
        if not tags:
            return {}
        for tag in tags:
            m = re.findall(ptn, str(tag.text))
            if m is None or len(m) == 0:
                continue
            storename = htmlparse.ParseItems.trimStr(m[0])
            if not storename:
                continue
            sidinf.storename = storename
            tag_a = tag.select_one("a")
            if not tag_a:
                continue
            sidinf.url = "https://www.suruga-ya.jp" + tag_a["href"]
            m = re.findall(r"[1-9][0-9]+", tag_a["href"])
            if not m:
                return {}
            sidinf.shop_id = int(m[0])
            return {storename: sidinf}
        return {}


class SurugayaParse(htmlparse.ParseItems):
    soup: BeautifulSoup
    parse: AB_SurugayaParse
    postage: SurugayaMakepurePostage

    def __init__(self, fp, id: int, date: datetime, url: str):
        self.soup = BeautifulSoup(fp, "html.parser")
        self.parse = self.createObj(self.soup, id, date, url)
        self.postage = SurugayaMakepurePostage(soup=self.soup)

    def createObj(self, soup: BeautifulSoup, id: int, date: datetime, url: str):
        if is_makepure(soup):
            return SurugayaProduct_Other(soup, id, date, url)
        else:
            return SurugayaProduct(soup, id, date, url)

    def getItems(self):
        return self.parse.getItems()

    def hasPostage(self) -> bool:
        return len(self.postage.get_ParseStorePostage()) > 0

    def getPostageList(self) -> list[htmlparse.ParseStorePostage]:
        return self.postage.get_ParseStorePostage()

    def hasShopIDInfo(self) -> bool:
        return len(self.postage.get_ParseShopIDInfo()) > 0

    def getShopIDInfo(self) -> dict[str, htmlparse.ParseShopIDInfo]:
        return self.postage.get_ParseShopIDInfo()


class SurugayaShiharaiParse:
    pos_list: list[htmlparse.ParseStorePostage]

    def __init__(self, fp):
        soup = BeautifulSoup(fp, "html.parser")
        self.pos_list = self.situmon_parse(soup)

    def get_ParseStorePostage(self):
        return self.pos_list

    def situmon_parse(self, soup: BeautifulSoup):
        results: set[htmlparse.ParseStorePostage] = set()
        situmon_list = soup.select(r".yokuarusitumon ul")
        for situmon in situmon_list:
            tagid = situmon.select_one(r"#shiharai_1_2")
            if not tagid:
                continue
            answer = situmon.select_one(r"li.answer")
            if not answer:
                continue
            text_list = answer.text.split("\n")
            psp: htmlparse.ParseStorePostage | None = None
            for text in text_list:
                if "■" in text:
                    raw_pref_list = text.replace("■", "").split("・")
                    pref_list = self.convert_to_pref_name(raw_pref_list)
                    psp = htmlparse.ParseStorePostage()
                    psp.storename = DEFAULT_STORENAME
                    psp.set_prefectures(pref_list)
                    continue
                if "お買上金額" in text:
                    m = re.findall(
                        r"([1-9][0-9]+)円?(未満|以上)(([1-9][0-9]+)(未満|以上))?…(無料|[1-9][0-9]+円)",
                        text.replace(",", ""),
                    )
                    if not m:
                        continue
                    boundary = self.get_boundary(m)
                    postage = self.get_postage(m)
                    if not boundary or postage is None:
                        continue
                    terms = htmlparse.ParsePostageTerms()
                    terms.boundary = boundary
                    terms.postage = postage
                    psp.add_terms(terms)
                    results.add(psp)
        return list(results)

    def get_postage(self, m):
        if m[0][5] == "":
            return None
        if str(m[0][5]) == "無料":
            return 0
        if "円" in m[0][5]:
            return int(str(m[0][5]).replace("円", ""))

    def get_boundary(self, m):
        if not m[0][0].isdigit() or not m[0][1]:
            return ""
        if m[0][3] and m[0][4]:
            return postage_data.ShippingTermsBoundary.create_boundary_of_db(
                lower_ope=self.convert_to_operator(str(m[0][1])),
                lower_val=int(m[0][0]),
                upper_ope=self.convert_to_operator(str(m[0][4])),
                upper_val=int(m[0][3]),
            )
        else:
            return postage_data.ShippingTermsBoundary.create_boundary_of_db(
                lower_ope=self.convert_to_operator(str(m[0][1])),
                lower_val=int(m[0][0]),
            )

    def convert_to_operator(self, text: str):
        match text:
            case "未満":
                return ">"
            case "以上":
                return "<="

    def convert_to_pref_name(self, raw_pref_list: list[str]):
        honshu = [
            "青森県",
            "岩手県",
            "宮城県",
            "秋田県",
            "山形県",
            "福島県",
            "茨城県",
            "栃木県",
            "群馬県",
            "埼玉県",
            "千葉県",
            "東京都",
            "神奈川県",
            "新潟県",
            "富山県",
            "石川県",
            "福井県",
            "山梨県",
            "長野県",
            "岐阜県",
            "静岡県",
            "愛知県",
            "三重県",
            "滋賀県",
            "京都府",
            "大阪府",
            "兵庫県",
            "奈良県",
            "和歌山県",
            "鳥取県",
            "島根県",
            "岡山県",
            "広島県",
            "山口県",
        ]
        shikoku = ["徳島県", "香川県", "愛媛県", "高知県"]
        kyushu = [
            "福岡県",
            "佐賀県",
            "長崎県",
            "熊本県",
            "大分県",
            "宮崎県",
            "鹿児島県",
            # "沖縄県",
        ]
        results: list[str] = []
        for rpref in raw_pref_list:
            if "本州" == rpref:
                results.extend(honshu)
            if "四国" == rpref:
                results.extend(shikoku)
            if "九州" == rpref:
                results.extend(kyushu)
            if "沖縄" == rpref:
                results.append("沖縄県")
            if "北海道" == rpref:
                results.append(rpref)
        return results
