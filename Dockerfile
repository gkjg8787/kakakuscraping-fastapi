FROM debian:bookworm

RUN apt-get update

RUN apt-get install -y tzdata
ENV TZ=Asia/Tokyo
RUN ln -sf /usr/share/zoneinfo/Japan /etc/localtime && \
    echo $TZ > /etc/timezone

RUN apt-get install -y python3

RUN apt-get install -y \
    python3-pip sqlite3 python3-venv procps

WORKDIR /app

COPY requirements.txt ./

RUN python3 -m venv /app/venv && . /app/venv/bin/activate && pip install -Ur requirements.txt

ENV PATH /app/venv/bin:$PATH

COPY . .

RUN mkdir -p tempdata/log && mkdir -p tempdata/html && mkdir db

EXPOSE 8000

WORKDIR /app/kakaku

RUN python3 db_util.py create && python3 dl_itemcomb_bin.py

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]