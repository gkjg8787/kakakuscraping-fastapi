import tarfile
import os

BASE_PATH = "data"
BASE_EXTENSION = ".tgz"


def read_tgz(filename: str):
    with tarfile.open(
        os.path.join(os.path.dirname(__file__), BASE_PATH + BASE_EXTENSION), "r:gz"
    ) as tar:
        try:
            f_member = tar.getmember(os.path.join(BASE_PATH, filename))
            if f_member.isfile():
                extracted_file = tar.extractfile(f_member).read().decode("utf-8")
                return extracted_file
            else:
                return None
        except KeyError:
            return None
    return None
