FROM python:3.8-slim

WORKDIR /usr/src/app

COPY makler/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["scrapy", "crawl"]
