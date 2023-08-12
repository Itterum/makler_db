require('dotenv').config();

// Имя базы данных
var dbName = process.env.MONGO_DB_NAME || "mydb";

// Создание базы данных
db = db.getSiblingDB(dbName);

// Создание пользователя в базе данных admin
db.getSiblingDB("admin").createUser({
  user: process.env.MONGO_INITDB_ROOT_USERNAME,
  pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
  roles: [
    { role: "root", db: "admin" },
  ]
});

// Создание пользователя в базе данных mydb
db.createUser({
  user: process.env.MONGO_INITDB_ROOT_USERNAME,
  pwd: process.env.MONGO_INITDB_ROOT_PASSWORD,
  roles: [
    { role: "readWrite", db: dbName },
  ]
});

console.log("Username:", process.env.MONGO_INITDB_ROOT_USERNAME);
console.log("Password:", process.env.MONGO_INITDB_ROOT_PASSWORD);
