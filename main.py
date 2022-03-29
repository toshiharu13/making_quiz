import logging
from pathlib import Path


def open_file(file):
    logging.info(f'в функцию open_file передано - {file}')
    with open(file, 'r', encoding='KOI8-R') as quiz_file:
        file_content = quiz_file.read()
        print(file_content)


def main():
    quiz_folder = 'quiz-questions'
    quiz_file = 'idv10.txt'
    quiz_full_path = Path.cwd()/quiz_folder/quiz_file

    open_file(quiz_full_path)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
        filename='logs.lod',
        filemode='w',
    )
    main()
