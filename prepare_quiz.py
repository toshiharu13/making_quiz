import logging
import re


def get_additional_split(string):
    logging.info(f'функция {get_additional_split.__name__} принимает {string}')
    result = re.split(r'\n', string, maxsplit=1)
    cleared_string = result[1]
    logging.info(
        f'функция {get_additional_split.__name__} возвращает {cleared_string}')
    return cleared_string


def normalize_quiz(splitted_quiz):
    logging.info(
        f'функция {normalize_quiz.__name__} принимает {splitted_quiz}')
    normalized_quiz = {}
    question = ''
    for question_block in splitted_quiz:
        if re.match(r'Вопрос \d', question_block):
            question = get_additional_split(question_block)
            continue
        if re.match(r'Ответ:', question_block):
            answer = get_additional_split(question_block)
            try:
                normalized_quiz[question] = answer
                question, answer = '', ''
            except BaseException as error:
                logging.error(
                    f'Ошибка при нормализации данных викторины {error}')
    logging.info(
        f'функция {normalize_quiz.__name__} возвращает {normalized_quiz}')
    return normalized_quiz


def get_splitted_strings_from_file(file):
    logging.info(
        f'в функцию {get_splitted_strings_from_file.__name__} передан {file}')
    with open(file, 'r', encoding='KOI8-R') as quiz_file:
        file_content = quiz_file.read()
        patern = re.compile("\n\n")
        splitted_quiz = patern.split(file_content)
        logging.info(f'функция {get_splitted_strings_from_file.__name__} '
                     f'возвращает {splitted_quiz}')
        return splitted_quiz
