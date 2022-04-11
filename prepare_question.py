import logging
import random

logger = logging.getLogger(__name__)


def get_question(quiz, old_question=None, jump=False):
    current_question = old_question
    if jump or not current_question:
        current_question, current_answer = random.choice(list(quiz.items()))
        logger.info(f'Выбранные вопрос/ответ:'
                    f' {current_question} -  {current_answer}')

    return current_question
