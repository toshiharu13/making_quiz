import logging
import re
from pathlib import Path


def get_additional_split(string):
    result = re.split(r'\n', string, maxsplit=1)
    cleared_string = result[1]
    logging.info(f'Результат нормализации - {cleared_string}')
    return cleared_string



def create_dict_quiz(splitted_strings):
    dict_quiz = {}
    question = ''
    for string in splitted_strings:
        if re.match(r'Вопрос \d', string):
            question = get_additional_split(string)
            continue
        if re.match(r'Ответ:', string):
            answer = get_additional_split(string)
            try:
                dict_quiz[question] = answer
                question, answer = '', ''
            except BaseException as error:
                logging.error(f'Ошибка при заполнении словаря {error}')
    return dict_quiz



def get_splitted_strings_from_file(file):
    logging.info(f'в функцию get_splitted_strings_from_file - {file}')
    with open(file, 'r', encoding='KOI8-R') as quiz_file:
        file_content = quiz_file.read()
        patern = re.compile("\n\n")
        splitted_string = patern.split(file_content)
        logging.info(f'возвращаем {splitted_string}')
        return splitted_string


def main():
    quiz_folder = 'quiz-questions'
    quiz_file = 'idv10.txt'
    quiz_full_path = Path.cwd()/quiz_folder/quiz_file

    splitted_strings = get_splitted_strings_from_file(quiz_full_path)
    quiz_dict_question = create_dict_quiz(splitted_strings)
    print(quiz_dict_question)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
        filename='logs.lod',
        filemode='w',
    )
    main()
