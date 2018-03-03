import telebot
from telebot import types
import config
from pymongo import MongoClient
import random
from ast import literal_eval
import operator

bot = telebot.TeleBot(config.token)
client = MongoClient()
db = client['clients']
clients = db.get_collection("clients")

@bot.message_handler(commands=['start'])
def greeting(message):
    userCount = clients.find({"_id": message.from_user.id}).count()
    if userCount == 0:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
        button_loc = types.KeyboardButton(text="Отправить местоположение", request_location=True)
        keyboard.add(button_phone, button_loc)
        bot.send_message(message.chat.id,
                     "Привет. Я помогаю искать пропавших питомцев. \nЧтобы обеспечить поиск и нахождение, пожалуйста, сообщите нам свои контактные данные",
                     reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id,
                     "Загрузите фото питомца.")


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    if(message.text=="Я его потерял"):
        clients.update( { "photos.findMode":"notSet"},{"$set":{"photos.$.findMode":"lose"} })
        user = clients.find({"_id": message.from_user.id})
        # dogs = {}
        bot.send_message(message.chat.id, "Питомцы, похожие на вашего:")
        for userImages in user:
            bot.send_message(message.chat.id, "Похожие на эту фотографию:")
            senderPhoto = clients.find({"photos.path": img["path"]})
            for img in userImages["photos"]:
                # dogs[img["path"]] = compareDogs(img["path"], "wanted")
                finded = compareDogs(img["path"], "wanted")
                print(finded)
                for f in finded:
                    print(f)
                    senderPhoto = clients.find({"photos.path" : f})
                    bot.send_photo(message.chat.id, photo=open(f, 'rb'))
                    for sp in senderPhoto:
                        # print("senderPhoto=" +str(sp))
                        contact = literal_eval(sp["contact"])
                        bot.send_message(message.chat.id, "Контакт для связи:")
                        bot.send_contact(message.chat.id,contact["phone_number"],contact['first_name'])
                        # print("senderPhoto=" +str(sp))


         # print(str(dogs))
    elif(message.text=="Я его нашел"):
        clients.update({"photos.findMode": "notSet"}, {"$set": {"photos.$.findMode": "wanted"}})
        user = clients.find({"_id": message.from_user.id})
        for userImages in user:
            for img in userImages["photos"]:
                compareDogs(img["path"], "lose")
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

        clients.update({"_id":message.from_user.id},{"$push":{"photos":{"path":src, "path":src, "findMode":"notSet"}}},True,True)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row('Я его потерял')
        markup.row('Я его нашел')
        bot.send_message(message.chat.id, "Выберете вариант:", reply_markup=markup)
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
    return random.random()*100

if __name__ == '__main__':
    bot.polling(none_stop=True)
