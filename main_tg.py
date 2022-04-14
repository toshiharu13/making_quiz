import logging
import os
import random
from pathlib import Path

import redis
from environs import Env
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

#from prepare_question import get_question
from prepare_quiz import get_splitted_strings_from_file, normalize_quiz

HELP, QUIZ_KEYBOARD, CHECK_ANSWER = range(3)
logger = logging.getLogger(__name__)


def start(update, context):
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]

    update.message.reply_text(
        text=f'''Обнаружена база повстанцев!
        Для рестарта R2D2 дайте команду /clear
        Если 3CPO надоел, отключите его командой /end''',
        reply_markup=ReplyKeyboardMarkup(custom_keyboard))
    return QUIZ_KEYBOARD


def clear_base(update, context):
    current_user_id = update.effective_chat.id
    redis_db = context.bot_data['redis_db']
    count_key = f'{current_user_id}_count'
    redis_db.delete(current_user_id)
    redis_db.set(count_key, 0)

    update.message.reply_text(
        text='Бортовой компьютер очищен, уходим в гиперпространство!')


def end(update, context):
    message_text = 'Да прибудет с тобой сила! Её тёмная сторона!'
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
    if not users_question:
        users_question, _ = random.choice(
            list(normalized_quiz_question.items()))
    context.bot.send_message(
        chat_id=current_user_id,
        text=users_question)
    logger.info(f'Ответ на вопрос - {normalized_quiz_question[users_question]}')

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
    question, _ = random.choice(list(normalized_quiz_question.items()))
    redis_db.set(current_user_id, question)
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
            'Сила с тобою юный подаван! нажми панели «Новый вопрос»'
        )
        question = get_question(normalized_quiz_question, users_question, True)
        redis_db.set(current_user_id, question)
        new_score = int(redis_db.get(count_key)) + 1
        redis_db.set(count_key, new_score)
    else:
        bot_answer = 'Сегодня сила не благоволит тебе, попробуй еще!'

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
    all_quizes = []
    quiz_folder_path = Path.cwd()/quiz_folder
    tg_bot_key = env.str('TG_BOT_KEY')

    all_quiz_files = os.listdir(quiz_folder_path)
    for quiz_file in all_quiz_files:
        quiz_from_one_file = get_splitted_strings_from_file(
            f'{quiz_folder_path}/{quiz_file}')
        all_quizes += quiz_from_one_file
    final_normalized_quiz = normalize_quiz(all_quizes)

    updater = Updater(tg_bot_key)
    dispatcher = updater.dispatcher
    bot_data = {
        'normalized_quiz_question': final_normalized_quiz,
        'redis_db': redis_db}

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            QUIZ_KEYBOARD: [CommandHandler('end', end),
                            CommandHandler('clear', clear_base),
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
