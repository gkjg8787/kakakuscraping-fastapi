from abc import ABCMeta, abstractmethod


class URLCreator(metaclass=ABCMeta):
    @abstractmethod
    def setParameter(self, param):
        pass

    @abstractmethod
    def createURL(self) -> str:
        pass

    @abstractmethod
    def isExistCategory(self) -> bool:
        pass
