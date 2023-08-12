require('dotenv').config();

// Имя базы данных
var dbName = process.env.MONGO_DB_NAME || "mydb";

// Создание базы данных
db = db.getSiblingDB(dbName);

// Создание пользователя
db.createUser({
  user: process.env.MONGO_INITDB_ROOT_USERNAME,
  pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
  roles: [
    { role: "readWrite", db: dbName }
  ]
});
