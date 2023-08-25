FROM debian:bullseye

RUN apt-get update

RUN apt-get install -y tzdata
ENV TZ=Asia/Tokyo
RUN ln -sf /usr/share/zoneinfo/Japan /etc/localtime && \
    echo $TZ > /etc/timezone

RUN apt-get install -y python3

RUN apt-get install -y \
    python3-pip sqlite3 procps libpq-dev


WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p tempdata/log && mkdir -p tempdata/html && mkdir db

EXPOSE 8000

WORKDIR /app/kakaku


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--root-path=/kakaku", "--proxy-headers"]
