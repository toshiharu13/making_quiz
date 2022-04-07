import logging
import re

logger = logging.getLogger(__name__)


def get_question(quiz, id, redis_db, old_key=None):
    if old_key:
        try:
            quiz.pop(old_key)
        except Exception as error:
            logger.error(f'Ошибка при переходе на следующий вопрос {error}')
    currant_question = next(iter(quiz))
    redis_db.set(id, currant_question)
    logger.info(f'Выборка вопроса - {currant_question}')

    normalized_answer = re.split(r'\.', quiz[currant_question], maxsplit=1)[0]
    normalized_answer = re.split(r'\(', normalized_answer, maxsplit=1)[0]
    normalized_answer = re.sub(r'[\'\"]', '', normalized_answer).lower()
    quiz[currant_question] = normalized_answer
    logger.info(f' нормализация ответа - {normalized_answer}')
    return currant_question