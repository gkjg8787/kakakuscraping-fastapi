import sys
import re
from scrapingmanage import sendTask
from sendcmd import ScrOrder


def urlCheck(url):
    pattern = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    if re.match(pattern, url):
        return True
    else:
        return False


def main():
    argslen = len(sys.argv)
    if argslen < 2 or argslen > 3:
        print("ERROR PARAMETER_NUM")
        sys.exit()
    if ScrOrder.UPDATE_ACT_ALL == sys.argv[1]:
        sendTask(ScrOrder.UPDATE_ACT_ALL, "", "")
        return
    if urlCheck(sys.argv[1]):
        url = sys.argv[1]
    else:
        print("ERROR PARAMETER_URL")
        sys.exit()
    id = -1
    if argslen == 3:
        id = int(sys.argv[2])

    sendTask(ScrOrder.UPDATE, url, id)


if __name__ == "__main__":
    main()
