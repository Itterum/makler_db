import scrapy
import logging
from datetime import datetime
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from twisted.internet import task
from pymongo import MongoClient


class MaklerMdSpider(scrapy.Spider):
    name = "makler_md"
    allowed_domains = ["makler.md"]
    start_urls = [
        'https://makler.md/ru/ribnita/transport/cars?list&currency_id=5&order=date&direction=desc&list=detail']
    all_cars = []

    visited_pagination = False

    def parse(self, response, **kwargs):
        for car in self.parse_page(response):
            self.all_cars.append(car)  # Добавляем данные в общий список

        if not self.visited_pagination:
            self.visited_pagination = True
            next_pages = response.css(
                'ul#paginator_pagesList li a::attr(href)').getall()
            for next_page in next_pages:
                next_page_full_url = self.start_urls[0] + \
                    next_page.replace('?', '&')
                logging.info(
                    f"Переход на следующую страницу: {next_page_full_url}")
                yield scrapy.Request(next_page_full_url, callback=self.parse)

    def parse_page(self, response):
        cars = []
        for car_link in response.css('article'):
            title = car_link.css('.ls-detail_anUrl::text').get()
            url = car_link.css('a::attr(href)').get()
            price_text = car_link.css('.ls-detail_price::text').get()

            if title:
                title = title.strip()

            if not title:
                title = car_link.css('.detail_anUrlTitle span::text').get()
                if title:
                    title = title.strip()

            if title and price_text:
                # Разбиваем строку цены на число и валюту
                price_parts = price_text.split()
                if len(price_parts) == 3:
                    price_num = float(price_parts[0].replace(
                        ',', '') + price_parts[1].replace(',', ''))
                    currency = price_parts[2]
                    logging.info(f'{price_num} - {currency}')
                elif len(price_parts) == 2:
                    price_num = float(price_parts[0].replace(
                        ',', ''))
                    currency = price_parts[1]
                    logging.info(f'{price_num} - {currency}')
                else:
                    price_num = None
                    currency = None

                car_data = {
                    'title': title,
                    'url': response.urljoin(url),
                    'price_text': price_text.strip(),
                    'price_num': price_num,
                    'currency': currency
                }
                cars.append(car_data)

        return cars

    def closed(self, reason):
        # Получаем текущую дату и время
        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Используем MongoClient для подключения к MongoDB
        client = MongoClient('mongodb://mongodb:27017/')
        db = client['cars_db']  # Выбираем базу данных

        # Создаем имя коллекции на основе текущей даты
        collection_name = f'cars_{current_datetime}'
        cars_collection = db[collection_name]

        # Вставляем данные в созданную коллекцию
        cars_collection.insert_many(self.all_cars)
        self.all_cars = []


def run_crawl():
    runner = CrawlerRunner()
    runner.crawl(MaklerMdSpider)


l = task.LoopingCall(run_crawl)
l.start(3600)

reactor.run()
