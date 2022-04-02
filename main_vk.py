import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from environs import Env
import random


def main():
    env = Env()
    env.read_env()

    vk_session = vk_api.VkApi(token=env.str('VK_API_KEY'))
    vk = vk_session.get_api()

    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()  # Переход на вторую строку
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)


    vk.messages.send(
        peer_id=env.str('USER_ID'),
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard(),
        message=' Да прибудет с тобой сила!'
    )

    longpoll = VkLongPoll(vk_session)

if __name__ == '__main__':
    main()
