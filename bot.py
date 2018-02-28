import telebot
from telebot import types
import config

bot = telebot.TeleBot(config.token)

@bot.message_handler(commands=['start'])
def greeting(command):
    markup = types.ReplyKeyboardMarkup(resize_keyboard='true', one_time_keyboard='true')
    markup.row('Найти питомца')
    markup.row('Я нашел питомца')
    bot.send_message(command.chat.id, 'Я помогаю людям искать своих пропавших собак.', reply_markup=markup)

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    if (message.text == 'Найти питомца' or message.text == 'Я нашел питомца'):
        bot.send_message(message.chat.id, "Отправьте фото найденого пёсика")
    else:
        bot.send_message(message.chat.id, "stub")

@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    try:
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        src = file_info.file_path;
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.reply_to(message, "Мы уже ищем вашего питомца. \nФото будет отправлено всем подписчикам Вашего города.")

    except Exception as e:
        bot.reply_to(message, e)

if __name__ == '__main__':
     bot.polling(none_stop=True)