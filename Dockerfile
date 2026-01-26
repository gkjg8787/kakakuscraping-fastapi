FROM python:3.14-slim-trixie

RUN pip install uv

RUN apt-get update && apt-get install -y tzdata
ENV TZ=Asia/Tokyo
RUN ln -sf /usr/share/zoneinfo/Japan /etc/localtime && \
    echo $TZ > /etc/timezone


RUN apt-get install -y \
    sqlite3 procps

WORKDIR /app

COPY requirements.txt ./

RUN uv venv /app/venv && . /app/venv/bin/activate && uv pip install -r requirements.txt

ENV PATH=/app/venv/bin:$PATH

COPY . .

RUN mkdir -p tempdata/log && mkdir -p tempdata/html && mkdir db

EXPOSE 8000

WORKDIR /app/kakaku

RUN python3 db_util.py create

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]