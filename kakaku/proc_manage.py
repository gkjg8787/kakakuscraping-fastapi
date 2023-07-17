import sys
from proc import ctrl_scraping

def main(argv):
    ctrl_scraping.start_cmd(argv)
    return

if __name__ == '__main__':
    main(sys.argv)