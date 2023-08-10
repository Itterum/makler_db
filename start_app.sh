#!/bin/bash

sudo systemctl start docker

export BOT_TOKEN=$(cat env_file.txt)

docker-compose down

docker-compose up --build -d

echo "Приложение успешно запущено."

docker system prune
