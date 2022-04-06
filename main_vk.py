import logging
import random
import re
from pathlib import Path

import redis
import vk_api
from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll

from prepare_quiz import create_dict_quiz, get_splitted_strings_from_file

ANSWERS_COUNT = 0
logger = logging.getLogger(__name__)


def get_question(quiz, use_id, redis_db, old_key=None):
    if old_key:
        try:
            quiz.pop(old_key)
        except Exception as error:
            logging.error(error)
    currant_question = next(iter(quiz))
    redis_db.set(use_id, currant_question)
    logger.info(f'Выборка вопроса - {currant_question}')

    normalized_answer = re.split(r'\.', quiz[currant_question], maxsplit=1)[0]
    normalized_answer = re.split(r'\(', normalized_answer, maxsplit=1)[0]
    normalized_answer = re.sub(r'[\'\"]', '', normalized_answer).lower()
    quiz[currant_question] = normalized_answer
    logger.info(f' нормализация ответа - {normalized_answer}')
    return currant_question


def handle_new_question_request(event, vk_bot, quiz_dict_question, redis_db):
    logger.info(f'в ivent лежит {event.__dict__}')
    currant_user_id = event.user_id
    question = get_question(quiz_dict_question, currant_user_id, redis_db)

    vk_bot.messages.send(
        user_id=currant_user_id,
        message=question,
        random_id=random.randint(1, 1000))


def surender(event, vk_bot, quiz_dict_question, redis_db):
    currant_user_id = event.user_id
    users_question = redis_db.get(currant_user_id)
    answer = quiz_dict_question[users_question]
    text = f'Здесь империя вынуждена отступить! Ответ - {answer}'
    vk_bot.messages.send(
        user_id=currant_user_id,
        message=text,
        random_id=random.randint(1, 1000))
    question = get_question(quiz_dict_question, currant_user_id, redis_db,
                            users_question)
    logger.info(f'новый вопрос - {question}')
    vk_bot.messages.send(
        user_id=currant_user_id,
        message=question,
        random_id=random.randint(1, 1000))


def get_count(event, vk_bot):
    currant_user_id = event.user_id
    message_text = f'Ваш счет - {ANSWERS_COUNT}'
    vk_bot.messages.send(
        user_id=currant_user_id,
        message=message_text,
        random_id=random.randint(1, 1000))


def handle_solution_attempt(event, vk_bot, quiz_dict_question, redis_db):
    global ANSWERS_COUNT
    currant_user_id = event.user_id
    user_message = event.text
    users_question = redis_db.get(currant_user_id)
    answer = quiz_dict_question[users_question]

    if user_message == answer:
        bot_answer = (
            'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        )
        get_question(quiz_dict_question, currant_user_id, redis_db,
                                users_question)
        ANSWERS_COUNT += 1
    else:
        bot_answer = 'Неправильно… Попробуешь ещё раз?'

    vk_bot.messages.send(
        user_id=currant_user_id,
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
    redis_db = redis.Redis(host='localhost', port=6379, db=0,
                           decode_responses=True)
    quiz_folder = 'quiz-questions'
    quiz_file = 'idv10.txt'
    quiz_full_path = Path.cwd() / quiz_folder / quiz_file
    vk_session = vk_api.VkApi(token=env.str('VK_API_KEY'))
    vk_bot = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    splitted_strings = get_splitted_strings_from_file(quiz_full_path)
    quiz_dict_question = create_dict_quiz(splitted_strings)

    try:
        keyboard = VkKeyboard(one_time=False)

        keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

        keyboard.add_line()
        keyboard.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text == 'Новый вопрос':
                    handle_new_question_request(event, vk_bot,
                                                quiz_dict_question, redis_db)
                elif event.text == "Сдаться":
                    surender(event, vk_bot, quiz_dict_question, redis_db)
                elif event.text == "Мой счёт":
                    get_count(event, vk_bot)
                else:
                    handle_solution_attempt(event, vk_bot, quiz_dict_question,
                                            redis_db)
    except Exception as error:
        logger.error(f'Бот упал с ошибкой - {error}')


if __name__ == '__main__':
    main()
