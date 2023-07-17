
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    def toDict(self):
        dic = {}
        for col in self.__table__.columns:
            dic[col.name] = getattr(self, col.name)
        return dic


class Item(Base):
    __tablename__ = "items"

    item_id : Mapped[int] = mapped_column(primary_key=True)
    name : Mapped[str] = mapped_column(insert_default='no name')
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    def __repr__(self) -> str:
        return f"Item(item_id={self.item_id!r}, name={self.name!r}, created_at={self.created_at!r})"

class Url(Base):
    __tablename__ = "url"

    url_id : Mapped[int] = mapped_column(primary_key=True)
    urlpath : Mapped[str]
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())
    
    def __repr__(self) -> str:
        return f"Url(url_id={self.url_id!r}, urlpath={self.urlpath!r}, created_at={self.created_at!r})"

class UrlInItem(Base):
    __tablename__ = "siteupdate"

    item_id : Mapped[int] = mapped_column(primary_key=True)
    url_id : Mapped[int] = mapped_column(primary_key=True)
    active : Mapped[str]
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    def __repr__(self) -> str:
        return f"UrlInItem(item_id{self.item_id!r}, url_id={self.url_id!r}, active={self.active!r}, created_at={self.created_at!r})"

class PriceLog(Base):
    __tablename__ = "itemsprice"

    log_id : Mapped[int] = mapped_column(primary_key=True)
    url_id : Mapped[int]
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())
    uniqname : Mapped[str]
    usedprice : Mapped[int]
    newprice : Mapped[int]
    taxin : Mapped[str]
    onsale : Mapped[str]
    salename : Mapped[str] = mapped_column(nullable=True)
    issuccess : Mapped[str]
    trendrate : Mapped[float]
    storename : Mapped[str]

    def __repr__(self) -> str:
        return ( f"PriceLog("
                 f"log_id={self.log_id!r}, url_id={self.url_id!r}, created_at={self.created_at!r}"
                 f", uniqname={self.uniqname!r}, usedprice={self.usedprice!r}, newprice={self.newprice!r}"
                 f", taxin={self.taxin!r}, onsale={self.onsale!r}, salename={self.salename!r}"
                 f", issuccess={self.issuccess!r}, trendrate={self.trendrate!r}, storename={self.storename!r}"
                   " )")

class PriceLog_2days(Base):
    __tablename__ = "pricelog_2days"

    log_id : Mapped[int] = mapped_column(primary_key=True)
    url_id : Mapped[int]
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())
    uniqname : Mapped[str]
    usedprice : Mapped[int]
    newprice : Mapped[int]
    taxin : Mapped[str]
    onsale : Mapped[str]
    salename : Mapped[str] = mapped_column(nullable=True)
    issuccess : Mapped[str]
    trendrate : Mapped[float]
    storename : Mapped[str]

    def __repr__(self) -> str:
        return ( f"PriceLog_2days("
                 f"log_id={self.log_id!r}, url_id={self.url_id!r}, created_at={self.created_at!r}"
                 f", uniqname={self.uniqname!r}, usedprice={self.usedprice!r}, newprice={self.newprice!r}"
                 f", taxin={self.taxin!r}, onsale={self.onsale!r}, salename={self.salename!r}"
                 f", issuccess={self.issuccess!r}, trendrate={self.trendrate!r}, storename={self.storename!r}"
                   " )")
    
    def compare_self_to_pricelog(self, pricelog :PriceLog):
        if self.url_id != pricelog.url_id\
            or self.created_at != pricelog.created_at\
            or self.uniqname != pricelog.uniqname\
            or self.usedprice != pricelog.usedprice\
            or self.newprice != pricelog.newprice\
            or self.taxin != pricelog.taxin\
            or self.onsale != pricelog.onsale\
            or self.salename != pricelog.salename\
            or self.issuccess != pricelog.issuccess\
            or self.trendrate != pricelog.trendrate\
            or self.storename != pricelog.storename\
            :
            return False
        return True


class NewestItem(Base):
    __tablename__ = "newestitem"

    item_id : Mapped[int] = mapped_column(primary_key=True)
    url_id : Mapped[int] = mapped_column(nullable=True)
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())
    newestprice : Mapped[int]
    taxin : Mapped[str] = mapped_column(insert_default="0")
    onsale : Mapped[str] = mapped_column(insert_default="0")
    salename : Mapped[str] = mapped_column(nullable=True)
    trendrate : Mapped[str] = mapped_column(insert_default="0")
    storename : Mapped[str] = mapped_column(insert_default="")
    lowestprice : Mapped[int]

    def __repr__(self) -> str:
        return ( f"NewestItem(item_id={self.item_id!r}, url_id={self.url_id!r}, created_at={self.created_at!r}"
                        f", newestprice={self.newestprice!r}, taxin={self.taxin!r}, onsale={self.onsale!r}"
                        f", salename={self.salename!r}, trendrate={self.trendrate!r}, storename={self.storename!r}"
                        f", lowestprice={self.lowestprice!r}"
                    ")" )



class Group(Base):
    __tablename__ = "groups"

    group_id : Mapped[int] = mapped_column(primary_key=True)
    groupname : Mapped[str]
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    def __repr__(self) -> str:
        return f"Group(group_id={self.group_id!r}, groupname={self.groupname!r}, created_at={self.created_at!r})"

class GroupItem(Base):
    __tablename__ = "groupsitem"

    group_id : Mapped[int] = mapped_column(primary_key=True)
    item_id : Mapped[int] = mapped_column(primary_key=True)
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    def __repr__(self) -> str:
        return f"GroupItem(group_id={self.group_id!r}, item_id={self.item_id!r}, created_at={self.created_at!r})"


