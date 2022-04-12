import logging
import os
import random
from pathlib import Path

import redis
import vk_api
from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll

from prepare_question import get_question
from prepare_quiz import get_splitted_strings_from_file, normalize_quiz

logger = logging.getLogger(__name__)


def start(event, vk_bot):
    current_user_id = event.user_id
    vk_bot.messages.send(
        user_id=current_user_id,
        message=f'''Обнаружена база повстанцев!
        Для рестарта R2D2 дайте команту /clear''',
        random_id=random.randint(1, 1000))


def clear_base(event, vk_bot, redis_db):
    current_user_id = event.user_id
    count_key = f'{current_user_id}_count'
    redis_db.delete(current_user_id)
    redis_db.set(count_key, 0)

    vk_bot.messages.send(
        user_id=current_user_id,
        message='Бортовой компьютер очищен, уходим в гиперпространство!',
        random_id=random.randint(1, 1000))


def handle_new_question_request(event, vk_bot,
                                normalized_quiz_question, redis_db):
    logger.info(f'в event лежит {event.__dict__}')
    current_user_id = event.user_id
    users_question = redis_db.get(current_user_id)
    question = get_question(normalized_quiz_question, users_question)
    if not users_question:
        redis_db.set(current_user_id, question)

    vk_bot.messages.send(
        user_id=current_user_id,
        message=question,
        random_id=random.randint(1, 1000))


def surender(event, vk_bot, normalized_quiz_question, redis_db):
    current_user_id = event.user_id
    users_question = redis_db.get(current_user_id)
    answer = normalized_quiz_question[users_question]
    text = f'Здесь империя вынуждена отступить! Ответ - {answer}'
    vk_bot.messages.send(
        user_id=current_user_id,
        message=text,
        random_id=random.randint(1, 1000))
    question = get_question(normalized_quiz_question, users_question, True)
    redis_db.set(current_user_id, question)
    logger.info(f'новый вопрос - {question}')
    vk_bot.messages.send(
        user_id=current_user_id,
        message=question,
        random_id=random.randint(1, 1000))


def get_count(event, vk_bot, redis_db):
    current_user_id = event.user_id
    count_key = f'{current_user_id}_count'
    message_text = f'Ваш счет - {redis_db.get(count_key)}'
    vk_bot.messages.send(
        user_id=current_user_id,
        message=message_text,
        random_id=random.randint(1, 1000))


def handle_solution_attempt(event, vk_bot, normalized_quiz_question, redis_db):
    current_user_id = event.user_id
    count_key = f'{current_user_id}_count'
    user_message = event.text
    users_question = redis_db.get(current_user_id)
    answer = normalized_quiz_question[users_question]

    if user_message == answer:
        bot_answer = (
            'Сила с тобою юный подаван! нажми панели «Новый вопрос»')
        question = get_question(normalized_quiz_question, users_question, True)
        redis_db.set(current_user_id, question)
        new_score = int(redis_db.get(count_key)) + 1
        redis_db.set(count_key, new_score)
    else:
        bot_answer = 'Сегодня сила не благоволит тебе, попробуй еще!'

    vk_bot.messages.send(
        user_id=current_user_id,
        message=bot_answer,
        random_id=random.randint(1, 1000))


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
    vk_session = vk_api.VkApi(token=env.str('VK_API_KEY'))
    vk_bot = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    all_quiz_files = os.listdir(quiz_folder_path)
    for quiz_file in all_quiz_files:
        quiz_from_one_file = get_splitted_strings_from_file(
            f'{quiz_folder_path}/{quiz_file}')
        all_quizes += quiz_from_one_file
    final_normalized_quiz = normalize_quiz(all_quizes)

    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == '/start':
                start(event, vk_bot)
            elif event.text == '/clear':
                clear_base(event, vk_bot, redis_db)
            elif event.text == 'Новый вопрос':
                handle_new_question_request(event, vk_bot,
                                            final_normalized_quiz, redis_db)
            elif event.text == "Сдаться":
                surender(event, vk_bot, final_normalized_quiz, redis_db)
            elif event.text == "Мой счёт":
                get_count(event, vk_bot, redis_db)
            else:
                handle_solution_attempt(event, vk_bot, final_normalized_quiz,
                                        redis_db)


if __name__ == '__main__':
    main()
