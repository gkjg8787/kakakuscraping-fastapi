import os
from datetime import datetime, timezone

from pydantic import BaseModel

from accessor.read_sqlalchemy import Session
from accessor import store
from model import store as m_store
from common import filter_name, const_value, read_config, cmnlog
from itemcomb import prefecture


class CopyOnlineStoreToLocalConfig(BaseModel):
    is_auto_copy: bool = False
    copy_type: filter_name.OnlineStoreCopyTypeName | None = None
    prefecture_name: str = ""


class CopyOnlineStoreToLocalConfigFactory:

    @staticmethod
    def create(is_auto_copy: bool, copy_type: str, prefecture_name: str):
        ct = None
        if copy_type:
            for osct in filter_name.OnlineStoreCopyTypeName:
                if osct.qname.lower().replace("_", "") == copy_type.lower().replace(
                    "_", ""
                ):
                    ct = osct
                    break
        if ct is None:
            ValueError(f"not support copy_type={copy_type}")
        if prefecture_name not in prefecture.PrefectureName.get_all_prefecturename():
            ValueError(f"not support prefecture={prefecture_name}")
        return CopyOnlineStoreToLocalConfig(
            is_auto_copy=is_auto_copy, copy_type=ct, prefecture_name=prefecture_name
        )

    @classmethod
    def read_config(cls):
        setting_name = "auto copy of online store info to local"
        auto_set = read_config.get_auto_copy_of_online_store_info_to_local()
        if not auto_set:
            ValueError(f"Setting [{setting_name}] not exist")
        if "auto" in auto_set:
            ValueError(f"Setting [{setting_name}]->auto not exist")
        if "type" in auto_set:
            ValueError(f"Setting [{setting_name}]->type not exist")
        prefname = read_config.get_default_shipping_prefecture_name()
        if not prefname:
            ValueError("Setting default shipping prefecture name not exist")
        return cls.create(
            is_auto_copy=auto_set["auto"],
            copy_type=auto_set["type"],
            prefecture_name=prefname,
        )


class AutoCopyOnlineStoreToLocal:
    coslc: CopyOnlineStoreToLocalConfig = CopyOnlineStoreToLocalConfig()
    logger: cmnlog.logging.Logger
    logger_header: str

    def __init__(self, logger: cmnlog.logging.Logger):
        self.logger = logger
        self.logger_header = os.path.basename(__file__)
        try:
            self.coslc = CopyOnlineStoreToLocalConfigFactory.read_config()
        except ValueError as e:
            logger.warning(f"{self.logger_header} {str(e)}")
        logger.info(
            f"{self.logger_header} auto_copy_online_store_to_local={self.coslc.is_auto_copy}"
        )

    def start(self, db: Session):
        if not self.coslc.is_auto_copy:
            return
        self.logger.info(f"{self.logger_header} start auto_copy_online_store_to_local")
        OnlineStoreCopy.copy_online_store_postage_to_local(
            db=db, osct_id=self.coslc.copy_type.id, pref_name=self.coslc.prefecture_name
        )
        self.logger.info(f"{self.logger_header} end auto_copy_online_store_to_local")


class OnlineStoreCopy:

    @classmethod
    def copy_online_store_postage_to_local(
        cls, db: Session, osct_id: int, pref_name: str
    ):
        match osct_id:
            case filter_name.OnlineStoreCopyTypeName.OVERWRITE.id:
                return cls.overwrite_online_store_postage_to_local(db, pref_name)
            case filter_name.OnlineStoreCopyTypeName.FILL_BLANK.id:
                return cls.fill_blank_online_store_postage_to_local(db, pref_name)
            case filter_name.OnlineStoreCopyTypeName.UPDATE.id:
                return cls.update_online_store_postage_to_local(db, pref_name)
            case _:
                raise ValueError(
                    f"not support OnlineStoreCopyType Value id = {osct_id}"
                )

    @classmethod
    def get_online_and_local_store_postage(cls, db: Session, pref_name: str):
        online_dic: dict[str, list] = {}
        pref_name_list = [prefecture.PrefectureName.get_country_wide_name(), pref_name]
        for oso in store.OnlineStoreQuery.get_all_by_prefname(db, pref_name_list):
            dic = dict(oso._mapping.items())
            if dic["storename"] in online_dic:
                max_terms_id = max(
                    [temp["terms_id"] for temp in online_dic[dic["storename"]]]
                )
                if dic["terms_id"] and max_terms_id:
                    dic["terms_id"] = max_terms_id + 1
                online_dic[dic["storename"]].append(dic)
            else:
                if (
                    dic["terms_id"]
                    and int(dic["terms_id"]) != const_value.INIT_TERMS_ID
                ):
                    dic["terms_id"] = const_value.INIT_TERMS_ID
                online_dic[dic["storename"]] = [dic]
        local_dic: dict[str, list] = {}
        for s in store.StoreQuery.get_store_and_postage_all_utc(db):
            dic = dict(s._mapping.items())
            if dic["storename"] in local_dic:
                local_dic[dic["storename"]].append(dic)
            else:
                local_dic[dic["storename"]] = [dic]
        return online_dic, local_dic

    @classmethod
    def overwrite_online_store_postage_to_local(cls, db: Session, pref_name: str):
        online_dict, local_dict = cls.get_online_and_local_store_postage(db, pref_name)
        add_store_list: set[str] = set()
        add_postage_dict: dict[str, list[m_store.StorePostage]] = {}
        for storename, dic_list in online_dict.items():
            if storename not in local_dict:
                add_store_list.add(storename)
                store_id = None
            else:
                store_id = local_dict[storename][0]["store_id"]
            for dic in dic_list:
                if dic["terms_id"] is None:
                    continue
                if storename in add_postage_dict:
                    add_postage_dict[storename].append(
                        m_store.StorePostage(
                            store_id=store_id,
                            terms_id=dic["terms_id"],
                            boundary=dic["boundary"],
                            postage=dic["postage"],
                            created_at=dic["terms_created_at"],
                        )
                    )
                else:
                    add_postage_dict[storename] = [
                        m_store.StorePostage(
                            store_id=store_id,
                            terms_id=dic["terms_id"],
                            boundary=dic["boundary"],
                            postage=dic["postage"],
                            created_at=dic["terms_created_at"],
                        )
                    ]
        store.StoreQuery.delete_all_storepostage(db)
        store.StoreQuery.delete_store_by_not_in_storenames(
            db, storename_list=list(add_postage_dict.keys())
        )
        db_store_list = store.StoreQuery.add_storename_list(
            db, storename_list=list(add_store_list)
        )
        for st in db_store_list:
            if st.storename not in add_postage_dict:
                continue
            for addpos in add_postage_dict[st.storename]:
                if addpos.store_id:
                    continue
                addpos.store_id = st.store_id
        store.StoreQuery.add_postage_by_add_postage_dict(
            db, add_postage_dict=add_postage_dict
        )
        return cls.convert_to_dict_for_StoreForListContext(add_postage_dict)

    @classmethod
    def convert_to_dict_for_StoreForListContext(
        cls, postage_dict: dict[str, list[m_store.StorePostage]]
    ):
        res: list[m_store.StorePostage] = []
        store_id_to_name: dict[int, str] = {}
        store_id_to_created_at: dict[int, str] = {}
        now = datetime.now(timezone.utc)
        for storename, sp_list in postage_dict.items():
            if not sp_list:
                continue
            store_id = int(sp_list[0].store_id)
            store_id_to_name[store_id] = storename
            if not sp_list[0].created_at:
                store_id_to_created_at[store_id] = now
            else:
                store_id_to_created_at[store_id] = sp_list[0].created_at
            res.extend(sp_list)
        return {
            "res": res,
            "store_id_to_name": store_id_to_name,
            "store_id_to_created_at": store_id_to_created_at,
        }

    @classmethod
    def fill_blank_online_store_postage_to_local(cls, db: Session, pref_name: str):
        online_dict, local_dict = cls.get_online_and_local_store_postage(db, pref_name)
        add_store_list: list[str] = []
        add_to_local_storepos_dict: dict[str, list[m_store.StorePostage]] = {}
        for storename, online_list in online_dict.items():
            if storename not in local_dict:
                add_store_list.append(storename)
                store_id = None
            elif not cls.is_blank_terms_of_local_list(local_dict[storename]):
                continue
            else:
                store_id = int(local_dict[storename][0]["store_id"])
            for dic in online_list:
                if storename in add_to_local_storepos_dict:
                    add_to_local_storepos_dict[storename].append(
                        m_store.StorePostage(
                            store_id=store_id,
                            terms_id=dic["terms_id"],
                            boundary=dic["boundary"],
                            postage=dic["postage"],
                            created_at=dic["terms_created_at"],
                        )
                    )
                else:
                    add_to_local_storepos_dict[storename] = [
                        m_store.StorePostage(
                            store_id=store_id,
                            terms_id=dic["terms_id"],
                            boundary=dic["boundary"],
                            postage=dic["postage"],
                            created_at=dic["terms_created_at"],
                        )
                    ]
        db_store_list = store.StoreQuery.add_storename_list(
            db, storename_list=list(add_store_list)
        )
        for st in db_store_list:
            if st.storename not in add_to_local_storepos_dict:
                continue
            for addpos in add_to_local_storepos_dict[st.storename]:
                if addpos.store_id:
                    continue
                addpos.store_id = st.store_id
        store.StoreQuery.add_postage_by_add_postage_dict(
            db, add_postage_dict=add_to_local_storepos_dict
        )
        return cls.convert_to_dict_for_StoreForListContext(add_to_local_storepos_dict)

    @classmethod
    def is_blank_terms_of_local_list(cls, local_list: list):
        for dic in local_list:
            if dic["terms_id"] is None:
                return True
            if not dic["boundary"]:
                return True
        return False

    @classmethod
    def update_online_store_postage_to_local(cls, db: Session, pref_name: str):
        online_dict, local_dict = cls.get_online_and_local_store_postage(db, pref_name)
        add_store_list: list[str] = []
        add_to_local_storepos_dict: dict[str, list[m_store.StorePostage]] = {}
        del_local_storepos_dict: dict[str, list[m_store.StorePostage]] = {}

        for storename, online_list in online_dict.items():
            if storename not in local_dict:
                add_store_list.append(storename)
                store_id = None
            else:
                if cls._is_same_postage(online_list, local_dict[storename]):
                    continue
                store_id = int(local_dict[storename][0]["store_id"])
                del_local_storepos_dict[storename] = [
                    m_store.StorePostage(
                        store_id=item["store_id"],
                        terms_id=item["terms_id"],
                    )
                    for item in local_dict[storename]
                ]

            for dic in online_list:
                if storename in add_to_local_storepos_dict:
                    add_to_local_storepos_dict[storename].append(
                        m_store.StorePostage(
                            store_id=store_id,
                            terms_id=dic["terms_id"],
                            boundary=dic["boundary"],
                            postage=dic["postage"],
                            created_at=dic["terms_created_at"],
                        )
                    )
                else:
                    add_to_local_storepos_dict[storename] = [
                        m_store.StorePostage(
                            store_id=store_id,
                            terms_id=dic["terms_id"],
                            boundary=dic["boundary"],
                            postage=dic["postage"],
                            created_at=dic["terms_created_at"],
                        )
                    ]

        db_store_list = store.StoreQuery.add_storename_list(db, storename_list=list(add_store_list))
        for st in db_store_list:
            if st.storename not in add_to_local_storepos_dict:
                continue
            for addpos in add_to_local_storepos_dict[st.storename]:
                if addpos.store_id:
                    continue
                addpos.store_id = st.store_id

        for storename, del_list in del_local_storepos_dict.items():
            store.StoreQuery.delete_storepostage_by_store_id_and_terms_id(db, del_list)
        store.StoreQuery.add_postage_by_add_postage_dict(db, add_postage_dict=add_to_local_storepos_dict)
        return cls.convert_to_dict_for_StoreForListContext(add_to_local_storepos_dict)

    @classmethod
    def _is_same_postage(cls, online_list: list, local_list: list) -> bool:
        if len(online_list) != len(local_list):
            return False

        online_list.sort(key=lambda x: x["terms_id"])
        local_list.sort(key=lambda x: x["terms_id"])

        for online, local in zip(online_list, local_list):
            if online["boundary"] != local["boundary"]:
                return False
            if online["postage"] != local["postage"]:
                return False
        return True
