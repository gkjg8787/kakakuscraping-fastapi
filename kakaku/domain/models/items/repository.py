from abc import ABC, abstractmethod

from accessor.read_sqlalchemy import Session
from domain.models.items import items


class IItemCreateRepository(ABC):
    db: Session

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def save(self, item: items.ItemCreate):
        pass


class IItemUpdateRepository(ABC):
    db: Session

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def save(self, item: items.ItemUpdate):
        pass


class IItemsURLCreateRepository(ABC):
    db: Session

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def save(self, item: items.ItemsURLCreate):
        pass


class IPriceUpdateRepository(ABC):
    db: Session

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def save(self, parseinfos: items.ParseInfosUpdate):
        pass
