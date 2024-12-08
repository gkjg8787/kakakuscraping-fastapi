import subprocess
import re
from pydantic import BaseModel


flake_cmd = f"flake8 --exclude tests,{__file__} --max-line-length 119"

list_of_error_to_ignore = """
./accessor/read_sqlalchemy.py:7:1: F401 'sqlalchemy.orm.Session' imported but unused
./downloader/requestoption.py:7:120: E501 line too long (125 > 119 characters)
./itemcomb/surugaya_postage/const_value.py:1:120: E501 line too long (143 > 119 characters)
./proc/proc_status.py:79:61: E203 whitespace before ':'
./tool/create_pricelog_2days.py:7:1: E402 module level import not at top of file
./tool/create_pricelog_2days.py:8:1: E402 module level import not at top of file
./tool/ctrl_db_organizer.py:7:1: E402 module level import not at top of file
./tool/db_url_delete.py:9:1: E402 module level import not at top of file
./tool/db_url_delete.py:10:1: E402 module level import not at top of file
./tool/db_url_delete.py:11:1: E402 module level import not at top of file
./tool/db_url_update.py:10:1: E402 module level import not at top of file
./tool/db_url_update.py:14:1: E402 module level import not at top of file
./tool/db_url_update.py:16:1: E402 module level import not at top of file
./tool/db_url_update.py:17:1: E402 module level import not at top of file
./tool/get_surugaya_postage.py:8:1: E402 module level import not at top of file
./tool/sendtask_cmd.py:10:1: E402 module level import not at top of file
./tool/sendtask_cmd.py:11:1: E402 module level import not at top of file
./tool/sendtask_cmd.py:13:1: E402 module level import not at top of file
./url_search/netoff/netoffSearchOpt.py:35:9: E722 do not use bare 'except'
./url_search/surugaya/surugayaSearchOpt.py:36:9: E722 do not use bare 'except'
"""


def get_error_list_to_ignore():
    results: list[str] = []
    ptn = r".+\/(.+\.py)(:.+)"
    for msg in list_of_error_to_ignore.split("\n"):
        m = re.search(ptn, msg.strip())
        if not m:
            continue
        results.append(m[1] + m[2])
    return results


class LintResult(BaseModel):
    err_list_to_ignore_num: int
    err_cnt: int
    ignore_err_cnt: int
    err_msg_list: list[str]


def equal_error_msg(eli: list[str], msg: str):
    for e in eli:
        if e in msg:
            return True
    return False


def get_lint_result():
    eli = get_error_list_to_ignore()
    p = subprocess.run(
        flake_cmd.split(" "),
        encoding="utf-8",
        capture_output=True,
    )
    result = LintResult(
        err_list_to_ignore_num=len(eli), err_cnt=0, ignore_err_cnt=0, err_msg_list=[]
    )
    for ret in str(p.stdout).strip().split("\n"):
        if equal_error_msg(eli, ret):
            result.ignore_err_cnt += 1
            continue
        else:
            result.err_cnt += 1
            result.err_msg_list.append(ret)
    return result


def main():
    ret = get_lint_result()
    if ret.err_cnt == 0:
        print("no error message")
    else:
        for msg in ret.err_msg_list:
            print(msg)
    print(f"error_list_to_ignore_num={ret.err_list_to_ignore_num}")
    print(f"error_count={ret.err_cnt}, ignore_error_count={ret.ignore_err_cnt}")


if __name__ == "__main__":
    main()
