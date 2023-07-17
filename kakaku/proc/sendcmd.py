class SendCmd:
    def __init__(self, cmdstr, url, id):
        self.__cmdstr = cmdstr
        self.__url = url
        self.__id = id
    
    @property
    def cmdstr(self):
        return self.__cmdstr
    @cmdstr.setter
    def cmdstr(self, cmdstr):
        self.__cmdstr = cmdstr
    
    @property
    def url(self):
        return self.__url
    @url.setter
    def url(self, url):
        self.__url = url
    
    @property
    def id(self):
        return self.__id
    @id.setter
    def id(self, id):
        self.__id = id

class ScrOrder:
    START = 'START'
    END = 'END'
    UPDATE = 'UPDATE'
    UPDATE_ACT_ALL = 'UPDATE_ACT_ALL'
    DB_ORGANIZE_DAYS = 'DB_ORGANIZE_DAYS'
    DB_ORGANIZE_SYNC = 'DB_ORGANIZE_SYNC'
    ORDERLIST = (START,
                 END,
                 UPDATE,
                 UPDATE_ACT_ALL,
                 DB_ORGANIZE_DAYS,
                 DB_ORGANIZE_SYNC,
                 )
    

    