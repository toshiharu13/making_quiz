import logging
from pathlib import Path

import redis
from environs import Env
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler,
                          ConversationHandler, Filters, MessageHandler,
                          Updater)

from prepare_quiz import normalize_quiz, get_splitted_strings_from_file
from prepare_question import get_question

HELP, QUIZ_KEYBOARD, CHECK_ANSWER = range(3)
logger = logging.getLogger(__name__)


def start(update, context):
    current_user_id = update.effective_chat.id
    redis_db = context.bot_data['redis_db']
    count_key = f'{current_user_id}_count'
    redis_db.delete(current_user_id)
    redis_db.set(count_key, 0)

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


def handle_new_question_request(update, context):
    current_user_id = update.effective_chat.id
    normalized_quiz_question = context.bot_data['normalized_quiz_question']
    redis_db = context.bot_data['redis_db']
    users_question = redis_db.get(current_user_id)

    question = get_question(normalized_quiz_question,
                            current_user_id, redis_db, users_question)
    context.bot.send_message(
        chat_id=current_user_id,
        text=question)
    return QUIZ_KEYBOARD


def surender(update, context):
    current_user_id = update.effective_chat.id
    normalized_quiz_question = context.bot_data['normalized_quiz_question']
    redis_db = context.bot_data['redis_db']
    users_question = redis_db.get(current_user_id)
    answer = normalized_quiz_question[users_question]
    text = f'Здесь империя вынуждена отступить! Ответ - {answer}'
    context.bot.send_message(
        chat_id=current_user_id,
        text=text)
    question = get_question(normalized_quiz_question, current_user_id, redis_db,
                            users_question, True)
    context.bot.send_message(
        chat_id=current_user_id,
        text=question)
    return QUIZ_KEYBOARD


def get_count(update, context):
    current_user_id = update.effective_chat.id
    redis_db = context.bot_data['redis_db']
    count_key = f'{current_user_id}_count'
    text = f'Ваш счет - {redis_db.get(count_key)}'
    context.bot.send_message(
        chat_id=current_user_id,
        text=text)


def handle_solution_attempt(update, context):
    current_user_id = update.effective_chat.id
    count_key = f'{current_user_id}_count'
    user_message = update.message.text
    normalized_quiz_question = context.bot_data['normalized_quiz_question']
    redis_db = context.bot_data['redis_db']
    users_question = redis_db.get(current_user_id)
    answer = normalized_quiz_question[users_question]

    if user_message == answer:
        bot_answer = (
            'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        )
        get_question(normalized_quiz_question, current_user_id, redis_db,
                     users_question, True)
        new_score = int(redis_db.get(count_key)) + 1
        redis_db.set(count_key, new_score)
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
    redis_db = redis.Redis(host=env.str('REDIS_HOST', 'localhost'),
                           port=env.int('REDIS_PORT', 6379),
                           db=env.str('REDIS_DB', 0),
                           decode_responses=True)

    quiz_folder = 'quiz-questions'
    quiz_file = env.str('QUIZ_FILE')
    quiz_full_path = Path.cwd()/quiz_folder/quiz_file
    tg_bot_key = env.str('TG_BOT_KEY')

    splitted_strings = get_splitted_strings_from_file(quiz_full_path)
    normalized_quiz_question = normalize_quiz(splitted_strings)

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


if __name__ == '__main__':
    main()
