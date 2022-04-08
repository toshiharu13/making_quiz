import logging

logger = logging.getLogger(__name__)


def get_question(quiz, id, redis_db, old_key=None, jump=False):
    all_keys = list(quiz.keys())
    if old_key:
        currant_question = old_key
    else:
        currant_question = all_keys[0]
    currant_index = all_keys.index(currant_question)

    if jump:
        try:
            #currant_index += 1
            currant_question = all_keys[currant_index+1]
        except IndexError:
            logger.info('вопросы закончились давайте подсчитаем очки')
            currant_question = all_keys[currant_index]
    redis_db.set(id, currant_question)

    return currant_question