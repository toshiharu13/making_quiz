import logging
import re

logger = logging.getLogger(__name__)


def get_additional_split(string):
    logging.info(f'функция {get_additional_split.__name__} принимает {string}')
    result = string.split('\n', 1)
    cleared_string = result[1]
    logger.info(
        f'функция {get_additional_split.__name__} возвращает {cleared_string}')
    return cleared_string


def normalize_quiz(splitted_quiz):
    normalized_quiz = {}
    question = ''
    for question_block in splitted_quiz:
        if re.match(r'Вопрос \d', question_block):
            question = get_additional_split(question_block)
            continue
        if re.match(r'Ответ:', question_block):
            answer = get_additional_split(question_block)

            normalized_answer = re.split(r'\.', answer, maxsplit=1)[0]
            normalized_answer = re.split(r'\(', normalized_answer, maxsplit=1)[0]
            normalized_answer = re.sub(r'[\'\"]', '', normalized_answer).lower()

            normalized_quiz[question] = normalized_answer
            question, answer = '', ''
    logger.info(
        f'функция {normalize_quiz.__name__} возвращает {normalized_quiz}')
    return normalized_quiz


def get_splitted_strings_from_file(file):
    logger.info(
        f'в функцию {get_splitted_strings_from_file.__name__} передан {file}')
    with open(file, 'r', encoding='KOI8-R') as quiz_file:
        file_content = quiz_file.read()
        splitted_quiz = file_content.split('\n\n')
        logger.info(f'функция {get_splitted_strings_from_file.__name__} '
                     f'возвращает {splitted_quiz}')
        return splitted_quiz

