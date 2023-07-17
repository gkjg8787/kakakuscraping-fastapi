import sys

from os.path import dirname
parent_dir = dirname(dirname(__file__))
sys.path.append(parent_dir)

from itemcomb.surugaya_postage_util import cmdstart

def main():
    cmdstart(sys.argv)

if __name__ == '__main__':
    main()