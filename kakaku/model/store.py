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


class Store(Base):
    __tablename__ = "stores"

    store_id: Mapped[int] = mapped_column(primary_key=True)
    storename: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
    )

    def __repr__(self) -> str:
        return (
            "Store("
            f"store_id={self.store_id!r}"
            f", storename={self.storename!r}"
            f", created_at={self.created_at!r}"
            ")"
        )


class StorePostage(Base):
    __tablename__ = "store_postage"

    store_id: Mapped[int] = mapped_column(primary_key=True)
    terms_id: Mapped[int] = mapped_column(primary_key=True)
    boundary: Mapped[str]
    postage: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
    )

    def __repr__(self) -> str:
        return (
            "StorePostage("
            f"store_id={self.store_id!r}"
            f", terms_id={self.terms_id!r}"
            f", boundary={self.boundary!r}"
            f", postage={self.postage!r}"
            f", created_at={self.created_at!r}"
            ")"
        )


class OnlineStore(Base):
    __tablename__ = "online_stores"
    shop_id: Mapped[int] = mapped_column(primary_key=True)
    storename: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
    )

    def __repr__(self) -> str:
        return (
            "OnlineStore("
            f"shop_id={self.shop_id!r}"
            f", storename={self.storename!r}"
            f", created_at={self.created_at!r}"
            ")"
        )


class OnlineStorePostage(Base):
    __tablename__ = "online_store_postage"

    shop_id: Mapped[int] = mapped_column(primary_key=True)
    pref_id: Mapped[int] = mapped_column(primary_key=True)
    terms_id: Mapped[int] = mapped_column(primary_key=True)
    boundary: Mapped[str]
    postage: Mapped[int]
    campaign_msg: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
    )
    insert_proc_type: Mapped[int]

    def __repr__(self) -> str:
        return (
            "OnlineStorePostage("
            f"shop_id={self.shop_id!r}"
            f", pref_id={self.pref_id!r}"
            f", terms_id={self.terms_id!r}"
            f", boundary={self.boundary!r}"
            f", postage={self.postage!r}"
            f", campaign_msg={self.campaign_msg!r}"
            f", created_at={self.created_at!r}"
            f", insert_proc_type={self.insert_proc_type!r}"
            ")"
        )


class Prefecture(Base):
    __tablename__ = "prefecture"

    pref_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    def __repr__(self) -> str:
        return f"Prefecture(pref_id={self.pref_id!r}, name={self.name!r})"


class DailyOnlineShopInfo(Base):
    __tablename__ = "daily_online_shop_info"
    shop_id: Mapped[int] = mapped_column(primary_key=True)
    shop_name: Mapped[str]
    url: Mapped[str]
    insert_proc_type: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.CURRENT_TIMESTAMP()
    )

    def __repr__(self) -> str:
        return (
            "DailyOnlineShopInfo("
            f"shop_id={self.shop_id!r}"
            f", shop_name={self.shop_name!r}"
            f", url={self.url!r}"
            f", insert_proc_type={self.insert_proc_type!r}"
            f", created_at={self.created_at!r}"
            ")"
        )
