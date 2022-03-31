import logging
import re
import redis
from pathlib import Path
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, Bot
from environs import Env


def get_additional_split(string):
    result = re.split(r'\n', string, maxsplit=1)
    cleared_string = result[1]
    logging.info(f'Результат нормализации - {cleared_string}')
    return cleared_string



def create_dict_quiz(splitted_strings):
    dict_quiz = {}
    question = ''
    for string in splitted_strings:
        if re.match(r'Вопрос \d', string):
            question = get_additional_split(string)
            continue
        if re.match(r'Ответ:', string):
            answer = get_additional_split(string)
            try:
                dict_quiz[question] = answer
                question, answer = '', ''
            except BaseException as error:
                logging.error(f'Ошибка при заполнении словаря {error}')
    return dict_quiz


def get_splitted_strings_from_file(file):
    logging.info(f'в функцию get_splitted_strings_from_file - {file}')
    with open(file, 'r', encoding='KOI8-R') as quiz_file:
        file_content = quiz_file.read()
        patern = re.compile("\n\n")
        splitted_string = patern.split(file_content)
        logging.info(f'возвращаем {splitted_string}')
        return splitted_string


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Обнаружена база повстанцев!")
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Выдвинуть свободный флот в квадрат дельта!',
        reply_markup=reply_markup)


def help(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=" Учебный бот для проведения олимпиад")


def get_question(quiz, id, redis_db):
    currant_question = next(iter(quiz))
    redis_db.set(id, currant_question)
    #print((redis_db.get(id)).decode('utf-8'))
    return currant_question


def echo(update, context):
    currant_user_id = update.effective_chat.id
    user_message = update.message.text
    quiz_dict_question = context.bot_data['quiz_dict_question']
    redis_db = context.bot_data['redis_db']
    users_question = redis_db.get(currant_user_id)
    answer = quiz_dict_question[users_question]
    #print(answer)
    logging.info(f'в функцию echo передан словарь {quiz_dict_question}')

    if user_message == 'Новый вопрос':
        question = get_question(quiz_dict_question, currant_user_id, redis_db)
        context.bot.send_message(
            chat_id=currant_user_id,
            text=question)
    else:
        normalized_answer = re.split(r'\.', answer, maxsplit=1)[0]
        normalized_answer = re.split(r'\(', normalized_answer, maxsplit=1)[0]
        normalized_answer = re.sub(r'[\'\"]', '', normalized_answer).lower()
        print(normalized_answer)
        print(user_message)
        if user_message == normalized_answer:
            bot_answer = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        else:
            bot_answer = 'Неправильно… Попробуешь ещё раз?'

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=bot_answer)


def main():
    env = Env()
    env.read_env()

    redis_db = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

    quiz_folder = 'quiz-questions'
    quiz_file = 'idv10.txt'
    quiz_full_path = Path.cwd()/quiz_folder/quiz_file
    tg_bot_key = env.str('TG_BOT_KEY')

    splitted_strings = get_splitted_strings_from_file(quiz_full_path)
    quiz_dict_question = create_dict_quiz(splitted_strings)

    try:
        updater = Updater(tg_bot_key)
        dispatcher = updater.dispatcher
        bot_data = {
            'quiz_dict_question': quiz_dict_question,
            'redis_db': redis_db,}

        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help))

        dispatcher.add_handler(MessageHandler(Filters.text, echo))
        dispatcher.bot_data = bot_data

        updater.start_polling()
        updater.idle()

    except Exception as error:
        logging.error(f'Бот упал с ошибкой - {error}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
        filename='logs.lod',
        filemode='w',
    )
    logger = logging.getLogger(__name__)
    main()
