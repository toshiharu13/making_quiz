# Бот для викторины 
[![Python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
[![VK](https://img.shields.io/badge/вконтакте-%232E87FB.svg?&style=for-the-badge&logo=vk&logoColor=white)](https://vk.com/)
[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org/)
## Описание
Данная программа подключается к  [Telegram](https://telegram.org/) и [VK](https://vk.com), для проведения викторины.
## Как установить
 - Склонировать проект
```shell
git clone https://github.com/toshiharu13/making_quiz.git
```
 - установить и запустить [Redis](https://realpython.com/python-redis/)

 - Установить requirements.txt
```shell
pip install -r requirements.txt
```
 - Создать файл .env и заполнить в нем переменные:
 
```dotenv
TG_BOT_KEY = 'токен бота от имени которого будут идти оповещения'
```
```dotenv
VK_API_KEY = 'ID телеграм чата для администратора(куда будут передаваться технические сообщения)'
```
```dotenv
QUIZ_FILE = 'Название файла с вопросами, файлы можно посмотреть в папке quiz-questions'
```

## Запуск
Запуск телеграм бота
```shell
python main_tg.py
```
Запуск VK бота
```shell
python main_vk.py
```

## Цель проекта
Код написан в рамках самостоятельного проекта на онлайн-курсе для веб-разработчиков [Devman](https://dvmn.org).