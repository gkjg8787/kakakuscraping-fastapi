from abc import ABC, abstractmethod


from domain.models.items import items


class IItemCreateRepository(ABC):
    @abstractmethod
    def save(self, item: items.ItemCreate):
        pass


class IItemUpdateRepository(ABC):
    @abstractmethod
    def save(self, item: items.ItemUpdate):
        pass


class IItemsURLCreateRepository(ABC):
    @abstractmethod
    def save(self, item: items.ItemsURLCreate):
        pass


class IPriceUpdateRepository(ABC):
    @abstractmethod
    def save(self, parseinfos: items.ParseInfosUpdate):
        pass


class IURLtoItemsRepository(ABC):
    @abstractmethod
    def get(self, url: str):
        pass


class IItemGetRepository(ABC):
    @abstractmethod
    def get(self, filter: dict):
        pass
