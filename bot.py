import random
from ast import literal_eval

import PIL
import numpy as np
from PIL import Image
from keras.applications.vgg16 import VGG16
from keras.applications.resnet50 import ResNet50

from pymongo import MongoClient
import telebot
from telebot import types


import config

import telebot
import cherrypy
import config

bot = telebot.TeleBot(config.token)
client = MongoClient()
db = client['clients']
clients = db.get_collection("clients")


@bot.message_handler(commands=['start'])
def greeting(message):
    userCount = clients.find({"_id": message.from_user.id}).count()
    if userCount == 0:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
        keyboard.add(button_phone)
        bot.send_message(message.chat.id,
                         "Привет. Я помогаю искать пропавших питомцев. \nЧтобы обеспечить поиск и нахождение, пожалуйста, сообщите нам свои контактные данные",
                         reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id,
                         "Загрузите фото питомца.")


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    cl = clients.find({"_id": message.from_user.id}).count()
    if cl == 0:
        greeting(message)
        return
    if (message.text == "Я его потерял"):
        clients.update({"_id": message.from_user.id, "photos.findMode": "notSet"}, {"$set": {"photos.$.findMode": "lose"}})
        user = clients.find({"_id": message.from_user.id})
        # dogs = {}
        # bot.send_message(message.chat.id, "Питомцы, похожие на вашего:")
        bot.send_message(message.chat.id, "Ищу...")
        for userImages in user:
            for img in userImages["photos"]:
                # dogs[img["path"]] = compareDogs(img["path"], "wanted")
                finded = compareDogs(img["path"], "wanted")
                # bot.send_message(message.chat.id, "Похожий на эту фотографию:")
                bot.send_message(message.chat.id, "Похожий питомец:")
                print(img["path"])
                # bot.send_photo(message.chat.id, photo=open(img["path"], 'rb'))

                key_min = min(finded.keys(), key=(lambda k: finded[k]))
                print(finded)
                print(key_min)

                # for f in finded:
                senderPhoto = clients.find({"photos.path": key_min})
                bot.send_photo(message.chat.id, photo=open(key_min, 'rb'))
                for sp in senderPhoto:
                    # print("senderPhoto=" +str(sp))
                    contact = literal_eval(sp["contact"])
                    bot.send_message(message.chat.id, "Контакт для связи:")
                    bot.send_contact(message.chat.id, contact["phone_number"], contact['first_name'])
                    # print("senderPhoto=" +str(sp))

                    # print(str(dogs))
    elif (message.text == "Я его нашел"):
        clients.update({"_id": message.from_user.id, "photos.findMode": "notSet"}, {"$set": {"photos.$.findMode": "wanted"}}, multi=True)
    else:
        bot.send_message(message.chat.id, "Отправьте фото пёсика")


@bot.message_handler(content_types=["contact"])
def getUserInfo(message):
    contact = message.contact
    insertStr = {"_id": contact.user_id, "contact": str(contact)}
    print(insertStr)
    clients.insert(insertStr)
    bot.send_message(message.chat.id, "Мы получили ваши контактные данные. Загрузите фото",
                     reply_markup=telebot.types.ReplyKeyboardRemove())
    print("contact= " + str(contact))


@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    try:
        client = clients.find({"_id": message.from_user.id}).count()
        if client == 0:
            greeting(message)
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = file_info.file_path;
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        clients.update({"_id": message.from_user.id},
                       {"$push": {"photos": {"path": src, "path": src, "findMode": "notSet"}}}, True, True)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('Я его потерял')
        markup.row('Я его нашел')
        bot.send_message(message.chat.id, "Выберете вариант или прикрепите еще одну фотографию:", reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, e)


def compareDogs(wantedDog, findMode):
    dogs = {}
    imgs = clients.find({"photos.findMode": findMode})
    for imgInClient in imgs:
        for img in imgInClient["photos"]:
            dogImg = img["path"]
            probably = getProbably(wantedDog, dogImg)
            dogs[dogImg] = probably

    # dogs = sorted(dogs.items(), key=operator.itemgetter(1))
    # print(dogs)
    return dogs


def getProbably(dog1, dog2):
    imgs = [dog1, dog2]
    #model = VGG16(weights='imagenet', include_top=False, pooling="avg")
    model = ResNet50(weights='imagenet', include_top=False)

    preds_tested = []
    for im in range(len(imgs)):
        img = PIL.Image.open(imgs[im])
        # добавить извлечение морды
        img = img.resize((244, 244), Image.ANTIALIAS)
        img = np.asarray(img)

        x = np.expand_dims(img.copy(), axis=0)
        preds = model.predict(x)
        preds_tested.append(preds)

    return np.linalg.norm(preds_tested[0] - preds_tested[1])
    # return random.random()*100


if __name__ == '__main__':
    bot.polling(none_stop=True)
