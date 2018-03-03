import telebot
from telebot import types
import config
from pymongo import MongoClient
import os
import random
import operator

bot = telebot.TeleBot(config.token)
client = MongoClient()
db = client['clients']
clients = db.get_collection("clients")

@bot.message_handler(commands=['start'])
def greeting(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
    keyboard.add(button_phone)
    bot.send_message(message.chat.id,
                     "Привет. Я помогаю искать пропавших питомцев. \nЧтобы обеспечить поиск и нахождение, пожалуйста, сообщите нам свои контактные данные",
                     reply_markup=keyboard)


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    # bot.reply_to(message, "Мы уже ищем вашего питомца. \nФото будет отправлено всем подписчикам Вашего города.")
    if(message.text=="Я его потерял"):
        clients.update({"_id" : message.from_user.id}, {"$set": {"findMode": "wanted"}})
        user = clients.find({"_id": message.from_user.id})
        for document in user:
            compareDogs(document["photo"], "wanted")
    elif(message.text=="Я его нашел"):
        clients.update({"_id" : message.from_user.id}, {"$set": {"findMode": "lose"}})
        user = clients.find({"_id": message.from_user.id})
        for document in user:
            compareDogs(document["photo"], "lose")
    else:
        bot.send_message(message.chat.id, "Отправьте фото пёсика")

@bot.message_handler(content_types=["contact"])
def getUserInfo(message):
    contact = message.contact
    insertStr = {"_id":contact.user_id,"contact":str(contact)}
    print(insertStr)
    clients.insert(insertStr)
    bot.send_message(message.chat.id, "Мы получили ваши контактные данные. Загрузите фото", reply_markup=telebot.types.ReplyKeyboardRemove())
    print("contact= " + str(contact))


@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    try:
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        src = file_info.file_path;
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        clients.update({},{"$set" : {"photo":src}})
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('Я его потерял')
        markup.row('Я его нашел')
        bot.send_message(message.chat.id, "Выберете вариант:", reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, e)


def compareDogs(wantedDog, findMode):
    dogs = {}
    imgs = clients.find({"findMode": findMode})
    for img in imgs:
        img = img["photo"]
        probably = getProbably(wantedDog, img)
        dogs[img] = probably
    print(dogs)
    #
    # for file in os.listdir("photos"):
    #     if file.endswith(".jpg"):
    #         currentDog = os.path.join("photos")+"\\"+file
    #
    # dogs = sorted(dogs.items(), key=operator.itemgetter(1))
    # print(dogs)

def getProbably(dog1, dog2):
    return random.random()*100

if __name__ == '__main__':
    compareDogs(None, "lose")
    bot.polling(none_stop=True)
