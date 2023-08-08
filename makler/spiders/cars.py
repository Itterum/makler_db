import scrapy
import json
import logging
import os
from datetime import datetime


class CarsSpider(scrapy.Spider):
    name = 'carsspider'
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
            price = car_link.css('.ls-detail_price::text').get()

            if title:
                title = title.strip()

            if not title:
                title = car_link.css('.detail_anUrlTitle span::text').get()
                if title:
                    title = title.strip()

            if title and price:
                car_data = {
                    'title': title,
                    'url': response.urljoin(url),
                    'price': price.strip()
                }
                cars.append(car_data)

        return cars

    def closed(self, reason):
        # Определяем путь и имя файла на основе текущей даты и времени
        # Замените на путь к папке, в которой хотите сохранять файл
        output_folder = 'output_data'
        os.makedirs(output_folder, exist_ok=True)  # Создаем папку, если её нет
        current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_filename = f'{output_folder}/output_{current_datetime}.json'
        # Метод closed вызывается после завершения парсинга
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_cars, f, ensure_ascii=False, indent=4)
