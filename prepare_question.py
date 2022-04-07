import logging

logger = logging.getLogger(__name__)


def get_question(quiz, id, redis_db, old_key=None):
    if old_key:
        try:
            quiz.pop(old_key)
        except Exception as error:
            logger.error(f'Ошибка при переходе на следующий вопрос {error}')
    currant_question = next(iter(quiz))
    redis_db.set(id, currant_question)

    return currant_question