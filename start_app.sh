#!/bin/bash

export BOT_TOKEN=$(cat env_file.txt)

docker-compose up --build -d

echo "Приложение успешно запущено."

docker system prune
