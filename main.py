import logging
import re
from pathlib import Path
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from environs import Env


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


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Обнаружена база повстанцев!")



def help(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=" Учебный бот для проведения олимпиад")


def echo(update, context):
    user_message = update.message.text
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=user_message)
    #print(update)


def main():
    env = Env()
    env.read_env()

    quiz_folder = 'quiz-questions'
    quiz_file = 'idv10.txt'
    quiz_full_path = Path.cwd()/quiz_folder/quiz_file
    tg_bot_key = env.str('TG_BOT_KEY')

    splitted_strings = get_splitted_strings_from_file(quiz_full_path)
    quiz_dict_question = create_dict_quiz(splitted_strings)
    #print(quiz_dict_question)

    try:
        updater = Updater(tg_bot_key)
        dispatcher = updater.dispatcher
        # on different commands - answer in Telegram
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help))

        # on noncommand i.e message - echo the message on Telegram
        dispatcher.add_handler(MessageHandler(Filters.text, echo))

        updater.start_polling()
        updater.idle()

    except Exception as error:
        logging.error(f'Бот упал с ошибкой - {error}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s; %(levelname)s; %(name)s; %(message)s',
        filename='logs.lod',
        filemode='w',
    )
    logger = logging.getLogger(__name__)
    main()
