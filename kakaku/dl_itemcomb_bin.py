import os
import requests

url = "https://github.com/gkjg8787/Go-ItemCombSum/releases/latest/download/Go-ItemCombSum"

def download_file(url):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

def main():
    fname = download_file(url)
    fparmission = 0o755
    os.chmod(fname, fparmission)

if __name__ == "__main__":
    main()