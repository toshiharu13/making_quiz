import logging
import re
from pathlib import Path

import redis
from environs import Env
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler,
                          ConversationHandler, Filters, MessageHandler,
                          Updater)

from prepare_quiz import normalize_quiz, get_splitted_strings_from_file

HELP, QUIZ_KEYBOARD, CHECK_ANSWER = range(3)
ANSWERS_COUNT = 0
logger = logging.getLogger(__name__)


def start(update, context):
    redis_db = context.bot_data['redis_db']
    redis_db.flushdb()

    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]

    update.message.reply_text(
        text='Обнаружена база повстанцев!',
        reply_markup=ReplyKeyboardMarkup(custom_keyboard))
    return QUIZ_KEYBOARD


def end(update, context):
    message_text = 'Заходите ещё!'
    reply_markup = ReplyKeyboardRemove()
    chat_id = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_id,
        text=message_text,
        reply_markup=reply_markup)
    return ConversationHandler.END


def get_question(quiz, id, redis_db, old_key=None):
    if old_key:
        try:
            quiz.pop(old_key)
        except Exception as error:
            print(error)
    currant_question = next(iter(quiz))
    redis_db.set(id, currant_question)
    logger.info(f'Выборка вопроса - {currant_question}')

    normalized_answer = re.split(r'\.', quiz[currant_question], maxsplit=1)[0]
    normalized_answer = re.split(r'\(', normalized_answer, maxsplit=1)[0]
    normalized_answer = re.sub(r'[\'\"]', '', normalized_answer).lower()
    quiz[currant_question] = normalized_answer
    logger.info(f' нормализация ответа - {normalized_answer}')
    return currant_question


def handle_new_question_request(update, context):
    currant_user_id = update.effective_chat.id
    normalized_quiz_question = context.bot_data['normalized_quiz_question']
    redis_db = context.bot_data['redis_db']

    question = get_question(normalized_quiz_question, currant_user_id, redis_db)
    context.bot.send_message(
        chat_id=currant_user_id,
        text=question)
    return QUIZ_KEYBOARD


def surender(update, context):
    currant_user_id = update.effective_chat.id
    normalized_quiz_question = context.bot_data['normalized_quiz_question']
    redis_db = context.bot_data['redis_db']
    users_question = redis_db.get(currant_user_id)
    answer = normalized_quiz_question[users_question]
    text = f'Здесь империя вынуждена отступить! Ответ - {answer}'
    context.bot.send_message(
        chat_id=currant_user_id,
        text=text)
    question = get_question(normalized_quiz_question, currant_user_id, redis_db,
                            users_question)
    context.bot.send_message(
        chat_id=currant_user_id,
        text=question)
    return QUIZ_KEYBOARD


def get_count(update, context):
    currant_user_id = update.effective_chat.id
    text = f'Ваш счет - {ANSWERS_COUNT}'
    context.bot.send_message(
        chat_id=currant_user_id,
        text=text)


def handle_solution_attempt(update, context):
    global ANSWERS_COUNT
    currant_user_id = update.effective_chat.id
    user_message = update.message.text
    normalized_quiz_question = context.bot_data['normalized_quiz_question']
    redis_db = context.bot_data['redis_db']
    users_question = redis_db.get(currant_user_id)
    answer = normalized_quiz_question[users_question]

    if user_message == answer:
        bot_answer = (
            'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        )
        get_question(normalized_quiz_question, currant_user_id, redis_db,
                     users_question)
        ANSWERS_COUNT += 1
    else:
        bot_answer = 'Неправильно… Попробуешь ещё раз?'

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=bot_answer)
    return QUIZ_KEYBOARD


def main():
    env = Env()
    env.read_env()

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
        filename='logs.lod',
        filemode='w',
    )
    redis_db = redis.Redis(host='localhost', port=6379,
                           db=0, decode_responses=True)

    quiz_folder = 'quiz-questions'
    quiz_file = env.str('QUIZ_FILE')
    quiz_full_path = Path.cwd()/quiz_folder/quiz_file
    tg_bot_key = env.str('TG_BOT_KEY')

    splitted_strings = get_splitted_strings_from_file(quiz_full_path)
    normalized_quiz_question = normalize_quiz(splitted_strings)

    try:
        updater = Updater(tg_bot_key)
        dispatcher = updater.dispatcher
        bot_data = {
            'normalized_quiz_question': normalized_quiz_question,
            'redis_db': redis_db}

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                QUIZ_KEYBOARD: [CommandHandler("end", end),
                                MessageHandler(Filters.regex('^(Новый вопрос)$'),
                                               handle_new_question_request),
                                MessageHandler(Filters.regex('^(Сдаться)$'),
                                               surender),
                                MessageHandler(Filters.regex('^(Мой счёт)$'),
                                               get_count),
                                MessageHandler(Filters.regex('.*'),
                                               handle_solution_attempt)
                                ],
            },
            fallbacks=[CommandHandler("end", end)],)

        dispatcher.add_handler(conv_handler)
        dispatcher.bot_data = bot_data

        updater.start_polling()
        updater.idle()

    except Exception as error:
        logger.error(f'Бот упал с ошибкой - {error}')


if __name__ == '__main__':
    main()
