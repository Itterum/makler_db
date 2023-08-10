import logging
import json
import aiocron
import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from pymongo import MongoClient

# Установите токен вашего бота
BOT_TOKEN = os.environ.get("TOKEN")

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
        client = MongoClient('mongodb://mongodb:27017/')
        db = client['cars_db']  # Выбор базы данных
        collections = db.list_collection_names()

        # Выбираем самую свежую коллекцию
        latest_collection = max(collections)
        cars_collection = db[latest_collection]  # Выбор коллекции

        # Получение данных из коллекции
        scraped_data = list(cars_collection.find())
        scraped_data_list = []

        for el in scraped_data:
            scraped_data_list.append(json.loads(str(el).replace('ObjectId(', '').replace(')', '').replace('\'', '\"')))

        if len(scraped_data_list) != 0:
            # Создание временного JSON файла
            json_filename = 'scraped_data.json'
            with open(json_filename, 'w', encoding='utf-8') as json_file:
                json.dump(scraped_data_list, json_file,
                          ensure_ascii=False, indent=4)

            # Отправка ссылки на скачивание файла
            await bot.send_document(message.chat.id, types.InputFile(json_filename), caption='JSON файл с данными за последний сбор')
        else:
            await message.reply('База данных пуста.')
    except Exception as e:
        await message.reply(f'Произошла ошибка при обращении к базе данных: {e}')


# Метод для сравнения двух коллекций и вывода отличий

async def compare_collections(message: types.Message):
    try:
        # Подключение к базе данных MongoDB
        client = MongoClient('mongodb://mongodb:27017/')
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
        for doc1, doc2 in zip(docs1, docs2):
            if doc1['price_num'] != doc2['price_num']:
                differences.append(
                    f"{doc1['title']}: {doc1['price_text']} -> {doc2['price_text']}\nСсылка: {doc1['url']}")

        if differences:
            my_message = f'Различия в ценах:\n'
            for diff in differences:
                my_message += diff + '\n'
            logging.info(my_message)
            await message.reply(my_message)
        else:
            await message.reply(f'Нет различий в ценах.')

    except Exception as e:
        await message.reply(f'Произошла ошибка при обращении к базе данных: {e}')


@dp.message_handler(commands=['compare'])
async def start_comparison_schedule(message: types.Message):
    # Расписание: каждые 10 минут
    cron = aiocron.crontab('*/60 * * * *')
    cron(compare_collections_wrapper(message))


def compare_collections_wrapper(message):
    async def compare_collections_task():
        await compare_collections(message)

    return compare_collections_task


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
