import sys

from os.path import dirname

parent_dir = dirname(dirname(__file__))
sys.path.append(parent_dir)
import proc.db_organizer as p_org


def main():
    p_org.start_cmd(sys.argv)


if __name__ == "__main__":
    main()
