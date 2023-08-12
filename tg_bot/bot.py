import logging
import json
import aiocron
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from pymongo import MongoClient

# Установите токен вашего бота
BOT_TOKEN = os.environ.get("TOKEN")
MONGO_USERNAME = os.environ.get("MONGO_INITDB_ROOT_USERNAME")
MONGO_PASSWORD = os.environ.get("MONGO_INITDB_ROOT_PASSWORD")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Глобальная переменная для хранения времени последнего сбора данных
last_collection_time = None


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Я бот для парсинга объявлений.")


@dp.message_handler(commands=['parse'])
async def parse_cars(message: types.Message):
    try:
        # Подключение к базе данных MongoDB
        client = MongoClient(f'mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@mongodb:27017/')
        db = client['cars_db']  # Выбор базы данных
        collections = db.list_collection_names()

        # Выбираем самую свежую коллекцию
        latest_collection = max(collections)
        cars_collection = db[latest_collection]  # Выбор коллекции

        # Получение данных из коллекции
        scraped_data = list(cars_collection.find())
        scraped_data_list = []

        for el in scraped_data:
            el_dict = el.copy()

            # Преобразование ObjectId в строку
            el_dict['_id'] = str(el_dict['_id'])

            # Преобразование datetime в строку
            for key, value in el_dict.items():
                if isinstance(value, datetime):
                    # Форматирование даты и времени
                    el_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')

            scraped_data_list.append(el_dict)

        if len(scraped_data_list) != 0:
            # Создание временного JSON файла
            json_filename = 'scraped_data.json'
            with open(json_filename, 'w', encoding='utf-8') as json_file:
                json.dump(scraped_data_list, json_file,
                          ensure_ascii=False, indent=4)

            # Отправка ссылки на скачивание файла
            await bot.send_document(message.chat.id, types.InputFile(json_filename), caption='JSON файл с данными за последний сбор')
            logging.info('Сообщение отправлено успешно.')
        else:
            await message.reply('База данных пуста.')
    except Exception as e:
        await message.reply(f'Произошла ошибка при обращении к базе данных: {e}')


# Метод для сравнения двух коллекций и вывода отличий

async def compare_collections(message: types.Message):
    try:
        # Подключение к базе данных MongoDB
        client = MongoClient(f'mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@mongodb:27017/')
        db = client['cars_db']  # Выбор базы данных
        collections = db.list_collection_names()

        # Выбираем две последние коллекции
        latest_collections = sorted(collections)[-2:]

        if len(latest_collections) < 2:
            await message.reply('Недостаточно данных для сравнения.')
            return

        collection1, collection2 = latest_collections

        # Получаем документы из коллекций
        docs1 = list(db[collection1].find())
        docs2 = list(db[collection2].find())

        # Проходимся по документам и сравниваем их
        differences = []
        news = []

        for doc1, doc2 in zip(docs1, docs2):
            if doc1['url'] == doc2['url'] and doc1['price_num'] != doc2['price_num']:
                differences.append(
                    f"{doc1['title']}: {doc1['price_text']} -> {doc2['price_text']}\nСсылка: {doc1['url']}")

        for doc2 in docs2:
            found = False
            for doc1 in docs1:
                if doc1['url'] == doc2['url']:
                    found = True
                    break
            if not found:
                news.append(f"Новое объявление: {doc2['url']}")

        if differences:
            my_message = f'Различия в ценах:\n'
            for diff in differences:
                my_message += diff + '\n'
                logging.info(my_message)
                await message.reply(diff)
        else:
            await message.reply(f'Нет различий в ценах.')

        if news:
            for new in news:
                logging.info(new)
                await message.reply(new)
        else:
            logging.info(f'Нет новых объявлений.')
        
    except Exception as e:
        await message.reply(f'Произошла ошибка при обращении к базе данных: {e}')


@dp.message_handler(commands=['compare'])
async def start_comparison_schedule(message: types.Message):
    # Расписание: каждые 60 минут
    cron = aiocron.crontab('*/60 * * * *')
    cron(compare_collections_wrapper(message))


def compare_collections_wrapper(message):
    async def compare_collections_task():
        await compare_collections(message)

    return compare_collections_task


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
