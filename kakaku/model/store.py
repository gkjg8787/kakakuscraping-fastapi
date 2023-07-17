
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

    store_id : Mapped[int] = mapped_column(primary_key=True)
    storename : Mapped[str] 
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    def __repr__(self) -> str:
        return f"Store(store_id={self.store_id!r}, storename={self.storename!r}, created_at={self.created_at!r})"

class StorePostage(Base):
    __tablename__ = "store_postage"

    store_id : Mapped[int] = mapped_column(primary_key=True)
    terms_id : Mapped[int] = mapped_column(primary_key=True)
    boundary : Mapped[str]
    postage : Mapped[int]
    created_at : Mapped[datetime] = mapped_column(server_default=func.CURRENT_TIMESTAMP())

    def __repr__(self) -> str:
        return ( f"StorePostage(store_id={self.store_id!r}, terms_id={self.terms_id!r}, boundary={self.boundary!r}"
                            f", postage={self.postage!r}, created_at={self.created_at!r}"
                            ")" )
    
