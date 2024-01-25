import operator
from functools import partial


class SelectItem:
    name: str
    storename: str
    price: int

    def __init__(self, name, storename, price):
        self.name = name
        self.storename = storename
        self.price = int(price)

    def getName(self):
        return self.name

    def getStoreName(self):
        return self.storename

    def getPrice(self):
        return self.price


class SumItem:
    def __init__(self, storecatalog: list):
        self.items: list[SelectItem] = []
        self.stores: list[Store] = []
        self.storecatalog: list[Store] = storecatalog
        self.sums = {}

    def addItem(self, sitem: SelectItem):
        self.items.append(sitem)
        if not self.existStore(sitem.getStoreName()):
            self.stores.append(self.getStore(sitem.getStoreName()))

    def existStore(self, storename: str):
        for store in self.stores:
            if store.getName() == storename:
                return True
        return False

    def createSum(self):
        sums = {}
        for item in self.items:
            if not item.getStoreName() in sums.keys():
                sums[item.getStoreName()] = {"sum": 0, "postage": 0}
            sums[item.getStoreName()]["sum"] += int(item.getPrice())
        for store in self.stores:
            sums[store.getName()]["postage"] = int(
                store.getPostage(sums[store.getName()]["sum"])
            )
        self.sums = sums

    def getSum(self):
        if len(self.sums) == 0:
            self.createSum()
        allsum = 0
        for storename in self.sums.keys():
            allsum += int(self.sums[storename]["sum"]) + int(
                self.sums[storename]["postage"]
            )
        return allsum

    def printSum(self):
        print(self.getTextSum())

    def getTextSum(self):
        if len(self.sums) == 0:
            self.createSum()
        text = ""
        for storename in self.sums.keys():
            text += "{} : sum = {}".format(storename, self.sums[storename]["sum"])
            text += "\n" + "{} : postage = {}".format(
                storename, self.sums[storename]["postage"]
            )
            setitems = [
                i.getName() for i in self.items if i.getStoreName() == storename
            ]
            text += "\n" + "{} : item = {}".format(storename, ",".join(setitems))
        return text

    def getdict(self):
        if len(self.sums) == 0:
            self.createSum()
        result = {"sum_pos_in": self.getSum()}
        sum_postage = 0
        for storename in self.sums.keys():
            store_postage = int(self.sums[storename]["postage"])
            sum_postage += store_postage
            result[storename] = {"postage": store_postage}
            result[storename]["sum_pos_out"] = int(self.sums[storename]["sum"])
            setitems = [
                {"itemname": i.getName(), "price": i.getPrice()}
                for i in self.items
                if i.getStoreName() == storename
            ]
            # result[storename]['itemnames'] = ','.join(setitems)
            result[storename]["items"] = setitems
        result["sum_postage"] = sum_postage
        return result

    def getStore(self, storename: str):
        for store in self.storecatalog:
            if store.getName() == storename:
                return store
        return None

    def existItemName(self, itemname):
        for item in self.items:
            if itemname == item.getName():
                return True
        return False

    def getItemlen(self):
        return len(self.items)


class Store:
    def __init__(self, name):
        self.name = name
        self.postageopes = []

    def addPostage(self, storeope):
        self.postageopes.append(storeope)

    def getPostage(self, price):
        sumpostage = 0
        for ope in self.postageopes:
            sumpostage += ope.calc(price)
        return sumpostage

    def getName(self):
        return self.name


class StoreOperator:
    def __init__(self, ope, postage):
        self.ope = ope
        self.postage = int(postage)

    def calc(self, price):
        return int(self.postage) if self.ope(int(price)) else 0

    @classmethod
    def create(cls, boundary_val, ope_str, postage):
        ope = StoreOperator.createOperator(boundary_val, ope_str)
        return cls(ope, postage)

    @staticmethod
    def createOperator(bval, ope_str):
        ope = None
        if "<" == ope_str:
            ope = partial(operator.lt, int(bval))
        elif "<=" == ope_str:
            ope = partial(operator.le, int(bval))
        elif ">=" == ope_str:
            ope = partial(operator.ge, int(bval))
        elif ">" == ope_str:
            ope = partial(operator.gt, int(bval))
        else:
            raise ValueError("not support operator string : " + ope_str)
        return ope

    @classmethod
    def rangeBoundary(cls, ope1, ope2, price):
        return ope1(int(price)) and ope2(int(price))

    @classmethod
    def createRange(cls, bval1, opst_1, bval2, opst_2, postage):
        ope1 = StoreOperator.createOperator(bval1, opst_1)
        ope2 = StoreOperator.createOperator(bval2, opst_2)
        ope = partial(StoreOperator.rangeBoundary, ope1, ope2)
        return cls(ope, postage)
