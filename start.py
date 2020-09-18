import telebot
import config
import random
from random import shuffle
import pymongo
from pymongo import MongoClient
import pprint
from telebot import types
import requests
from grab import Grab

import os
from flask import Flask, request

bot = telebot.TeleBot(config.TOKEN)
server = Flask(__name__)

# client = MongoClient('localhost', 27017)
client = MongoClient(config.DB_CLIENT, retryWrites=False)
db = client['english_trainspoting']
# db = client['heroku_jq9wgddb']

usersCollection = db['users']
videoCollection = db['video_to_listen']
phraseCollection = db['make_phrase']

# pprint.pprint(list(collection.find({"year": "2019"})))

URL_AUTH = 'https://developers.lingvolive.com/api/v1.1/authenticate'
URL_TRANSLATE = 'https://developers.lingvolive.com/api/v1/Minicard'


# URL_TRANSLATE = 'https://developers.lingvolive.com/api/v1/Translation'


@bot.message_handler(commands=['filltheform'])
def formFilling(message):
    print(message)
    g = Grab()
    g.go('http://atthelesson.h1n.ru/health/index.php')
    # print(g.doc.body)
    g.doc.choose_form(name="dataInput")

    g.doc.set_input_by_id("studentId", "1657181")
    g.doc.set_input_by_id("lastname", "Рожков")
    g.doc.set_input_by_id("customRadio1", "Здоров")
    g.doc.set_input_by_id("customRadio3", "В РО")
    # g.doc.set_input_by_id("customRadio3", "Покинул РО")

    g.submit()
    msg = g.doc.text_search(u'отправлены')
    bot.send_message(message.chat.id, msg)
    # print(g.doc.text_assert(u'Ошибка'))


def addNewUserToDB(message):
    usersCollection.insert_one(
        {
            "id": str(message.from_user.id),
            "username": message.from_user.first_name,
            "role": "user",
            "current_britain_video_id": 1,
            "current_american_video_id": 1,
            "current_make_phrase_id": 1,
        }
    )
    new_user = username_db = usersCollection.find_one({"id": str(message.from_user.id)})
    print(new_user)


@bot.message_handler(commands=['start'])
def welcome(message):
    print(message)
    print(ord("❶"))
    print(chr(10105))
    print(ord("а"))
    pprint.pprint(os.environ.keys())
    global userDataDB, newVideoTaskFlag, newPhraseTaskFlag
    newVideoTaskFlag = False
    newPhraseTaskFlag = False
    userDataDB = usersCollection.find_one({"id": str(message.from_user.id)})

    username_from_message = message.from_user.first_name

    if userDataDB:
        msg = "И снова здравствуйте, " + str(username_from_message)
    else:
        addNewUserToDB(message)
        msg = "Рад познакомиться, " + str(username_from_message) + \
              "\nЯ - <b>{0.first_name}</b>, бот созданный помочь развить Ваш навык английского языка " \
              "\nИспользуйте кнопки внизу (или нажмите на квадрат с квадратиками) для перемещения. " \

    bot.send_message(message.chat.id, msg.format(bot.get_me()), parse_mode='html')
    mainMenuInit(message)


def mainMenuInit(message):
    global userDataDB
    # keyboard
    main_screen_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)

    # item1 = types.KeyboardButton("🎲 Рандомное число")
    item2 = types.KeyboardButton("😊 Как дела?")
    videoListening = types.KeyboardButton("О чем они говорят? 🤔")
    # main_screen_markup.row("🎲 Рандомное число", "😊 Как дела?")
    main_screen_markup.add( "О чем они говорят? 🤔",
                           "Составь ______ на английском",
                            "❓ Помощь")

    isAdmin = userDataDB.get("role")
    if isAdmin == "admin":
        main_screen_markup.add("📽 Добавить видео задание", "📝 Добавить фразу для составления")

    bot.send_message(message.chat.id, "Главное меню ⬇️⬇️⬇️", parse_mode='html', reply_markup=main_screen_markup)


@bot.message_handler(content_types=['video'])
def addNewVideoTask(message):
    global userDataDB, newVideoTaskFlag
    isAdmin = userDataDB.get("role")
    if isAdmin == "admin" and newVideoTaskFlag == True:
        newVideoTaskMass = message.caption.split("\n")
        newVideoTaskAccent = newVideoTaskMass[0]
        newVideoTaskAnswers = []
        for i in range(1, 5):
            newVideoTaskAnswers.append(newVideoTaskMass[i])
        newVideoTaskRightAnswer = newVideoTaskMass[1]
        newVideoTaskFileId = message.video.file_id
        videoCountsByCountry = videoCollection.count_documents(filter={"country_accent": str(newVideoTaskAccent)})
        newVideoTaskId = videoCountsByCountry + 1

        videoCollection.insert_one(
            {
                "id": str(newVideoTaskId),
                "country_accent": newVideoTaskAccent,
                "file_id": newVideoTaskFileId,
                "answers": newVideoTaskAnswers,
                "right_answer": newVideoTaskRightAnswer,
            }
        )
        newVideoTask = videoCollection.find_one({"id": str(newVideoTaskId)})
        print(newVideoTask)
    else:
        bot.send_message(message.chat.id, "У Вас нет прав на совершение данного действия")


# @bot.message_handler(content_types=['text'])
def addNewPhraseTask(message):
    global userDataDB, newPhraseTaskFlag
    isAdmin = userDataDB.get("role")
    print("Добавить новую фразу")
    if isAdmin == "admin" and newPhraseTaskFlag == True:
        newPhraseTaskMass = message.text.split("\n")
        newPhraseTaskQuestion = newPhraseTaskMass[0]
        print(newPhraseTaskQuestion)
        newPhraseTaskAnswer = newPhraseTaskMass[1]
        print(newPhraseTaskAnswer)
        phraseCounts = phraseCollection.estimated_document_count()
        newPhraseTaskId = phraseCounts + 1
        print(newPhraseTaskId)

        phraseCollection.insert_one(
            {
                "id": str(newPhraseTaskId),
                "question_sentence": newPhraseTaskQuestion,
                "answer_sentence": newPhraseTaskAnswer
            }
        )
        newPhraseTask = phraseCollection.find_one({"id": str(newPhraseTaskId)})
        print(newPhraseTask)
    else:
        bot.send_message(message.chat.id, "У Вас нет прав на совершение данного действия")


@bot.message_handler(content_types=['text'])
def mainScreenResponse(message):
    print(message)
    print(str(message.from_user.first_name) + " " + str(message.from_user.last_name) + ": " + str(message.text))
    global videoRightAnswer, newVideoTaskFlag
    global userCountryAccent
    global phraseBlankMessage, userPhraseItemChoice, makePhraseInlineMarkup, newPhraseTaskFlag
    if message.chat.type == 'private':
        if message.text == '🎲 Рандомное число':
            bot.send_message(message.chat.id, str(random.randint(0, 100)))

        elif message.text == "📽 Добавить видео задание":
            newVideoTaskMarkup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            newVideoTaskMarkup.row("📽 Новые видео добавлены")
            newVideoTaskFlag = True
            bot.send_message(message.chat.id, "Правила добавления новых видео заданий:\n"
                                              "1 строка - акцент <b>Britain</b> или <b>American</b>\n"
                                              "2, 3, 4, 5 строки - варианты ответов к загружаемому видео на русском\n"
                                              "Важно - вариант во второй строке должен быть верным ответом",
                             reply_markup=newVideoTaskMarkup, parse_mode="html")

        elif message.text == "📽 Новые видео добавлены":
            newVideoTaskFlag = False
            mainMenuInit(message)

        elif message.text == "📝 Добавить фразу для составления":
            newPhraseTaskMarkup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            newPhraseTaskMarkup.row("📝 Новые фразы добавлены")
            newPhraseTaskFlag = True
            bot.send_message(message.chat.id, "Правила добавления новых фраз для задания:\n"
                                              "1 строка - Изначальное предложение на русском\n"
                                              "2 строка - Правильно переведенный на английский, вариант первого предложения\n"
                                              "Важно - вариант во второй строке должен быть верным ответом",
                             reply_markup=newPhraseTaskMarkup, parse_mode="html")

        elif message.text == "📝 Новые фразы добавлены":
            newPhraseTaskFlag = False
            mainMenuInit(message)

        elif message.text == '😊 Как дела?':
            inline_markup = types.InlineKeyboardMarkup(row_width=2)
            item1 = types.InlineKeyboardButton("Хорошо", callback_data='good')
            item2 = types.InlineKeyboardButton("Не очень", callback_data='bad')
            inline_markup.add(item1, item2)
            bot.send_message(message.chat.id, 'Отлично, сам как?', reply_markup=inline_markup)

        elif message.text == "❓ Помощь":
            helpMarkup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            helpMarkup.row("На главную 🏠")
            bot.send_message(message.chat.id, "Как Вы наверное помните, я - English Trainspoting, бот, помогающий "
                                              "в развитии навыков понимания английского языка.\n"
                                              "Вот краткое пояснение того, что я умею:\n"
                                              "<b>О чем они говорят?</b> - задание для развития аудиального восприятия."
                                              " Послушайте о чем говорят герои видео, и выберите верный ответ.\n"
                                              "<b>Составь ______ на английском</b> - это задание поможет Вам научиться "
                                              "строить предложения. Взгляните на предложение на русском и попробуйте "
                                              "составить его из английских слов.\n"
                                              "Если Вам вдруг встретилось незнакомое английское слово или Вы хотите "
                                              "узнать как русское слово пишется по английски - просто напишите его в "
                                              "чат и я постараюсь Вам ответить.\n\n\n"
                                              "Я почему то долго не отвечаю на сообщения? Напишите в чат команду"
                                              " '<b>/start</b>'. Возможно что-то пошло не так\n"
                                              "В случае если Вы уверены ,что нашли ошибку или неработающее задание "
                                              "- напишите мне на почту flikson@gmail.com\n"
                                              "Заранее Вам спасибо и удачи в Ваших начинаниях ❤️",
                             reply_markup=helpMarkup, parse_mode="html")

        elif message.text == "На главную 🏠":
            mainMenuInit(message)

        elif message.text == "Составь ______ на английском" or message.text == "Еще фраз! 📝":
            makePhrase(message)

        elif message.text == "О чем они говорят? 🤔":
            countryAccentMarkup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            countryAccentMarkup.row("Британский 🇬🇧", "Американский 🇺🇸", "На главную 🏠")
            bot.send_message(message.chat.id, "С каким акцентом вы бы хотели сдружиться?",
                             reply_markup=countryAccentMarkup)
            videoRightAnswer = ""

        elif (message.text == "Британский 🇬🇧") or (message.text == "Американский 🇺🇸") or (
                message.text == "Еще разговоров! 🤐"):

            if message.text == "Британский 🇬🇧":
                userCountryAccent = "British"
            elif message.text == "Американский 🇺🇸":
                userCountryAccent = "American"

            videoRightAnswer = videoListening(message, userCountryAccent)
            print("о чем " + videoRightAnswer)

        elif ord(message.text[0]) in [10102, 10103, 10104, 10105]:
            print("проверка " + videoRightAnswer)

            if videoRightAnswer == message.text:
                bot.send_message(message.chat.id, "И это правильный ответ!")
                userCurrentVideoIdInc(message, userCountryAccent)
            else:
                bot.send_message(message.chat.id, "Увы, нет. Послушай еще раз.")

        else:
            if newPhraseTaskFlag == False:
                msg = getWordTranslation(message.text)
                bot.send_message(message.chat.id, msg)
            else:
                addNewPhraseTask(message)


def makePhrase(message):
    global phraseBlankMessage, makePhraseInlineMarkup, phraseEditedMessage, phraseAnswer

    phraseCounts = phraseCollection.estimated_document_count()
    print("Phrase counts " + str(phraseCounts))
    randomPhraseId = random.randint(1, phraseCounts)

    userCurrentMakePhraseId = usersCollection.find_one({"id": str(message.from_user.id)}).get("current_make_phrase_id")
    print("user current make phrase id: " + str(userCurrentMakePhraseId))

    if userCurrentMakePhraseId <= phraseCounts:
        phraseDataDB = phraseCollection.find_one({"id": str(userCurrentMakePhraseId)})
    else:
        phraseDataDB = phraseCollection.find_one({"id": str(randomPhraseId)})

    phraseQuestion = phraseDataDB.get("question_sentence")
    print(phraseQuestion)
    phraseAnswer = phraseDataDB.get("answer_sentence")
    print(phraseAnswer)
    answersMass = phraseAnswer.split()
    shuffle(answersMass)
    print(answersMass)

    makePhraseInlineMarkup = types.InlineKeyboardMarkup()
    phraseBlankMessage = ""
    callbackData = "phrase_word:"
    for elem in answersMass:
        userPhraseItemChoice = types.InlineKeyboardButton(elem, callback_data=callbackData + elem)
        makePhraseInlineMarkup.add(userPhraseItemChoice)
        phraseBlankMessage += "___ "

    makePhraseInlineMarkup.row(types.InlineKeyboardButton("✅", callback_data=callbackData + "✅"),
                               types.InlineKeyboardButton("❌", callback_data=callbackData + "❌"))
    phraseEditedMessage = phraseBlankMessage

    makePhraseMarkup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    makePhraseMarkup.add("Еще фраз! 📝", "На главную 🏠")

    bot.send_message(message.chat.id, phraseQuestion, reply_markup=makePhraseMarkup)
    bot.send_message(message.chat.id, phraseBlankMessage, reply_markup=makePhraseInlineMarkup)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == 'good':
                bot.send_message(call.message.chat.id, 'Вот и отличненько 😊')
            elif call.data == 'bad':
                bot.send_message(call.message.chat.id, 'Бывает 😢')

            elif call.data[0:11] == "phrase_word":
                global phraseBlankMessage, phraseEditedMessage, makePhraseInlineMarkup, phraseAnswer
                userPhraseChoice = call.data[12:]
                if userPhraseChoice == "✅":
                    print("Confirm" + str(userPhraseChoice))
                    print(phraseEditedMessage)
                    print(phraseAnswer)
                    userPhraseChoice = ""
                    if str(phraseEditedMessage) == str(phraseAnswer):
                        msg = "Да, вы абсолютно правы!"
                        userCurrentMakePhraseIdInc(call)
                    else:
                        msg = "Увы, но нет. Подумайте хорошенько"

                    bot.send_message(chat_id=call.message.chat.id,
                                     text=msg)

                elif userPhraseChoice == "❌":
                    print("Clear")
                    phraseEditedMessage = phraseBlankMessage
                    bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=phraseEditedMessage,
                                          reply_markup=makePhraseInlineMarkup)
                else:
                    print("userPhraseChoice: " + str(userPhraseChoice))
                    phraseEditedMessage = phraseEditedMessage.replace("___", userPhraseChoice, 1)
                    print(phraseEditedMessage)
                    # print(bot.chosen_inline_handlers)
                    bot.edit_message_text(chat_id=call.message.chat.id,
                                          message_id=call.message.message_id,
                                          text=phraseEditedMessage,
                                          reply_markup=makePhraseInlineMarkup)

                # show alert
                # bot.answer_callback_query(callback_query_id=call.id, show_alert=False,
                #                           text="ЭТО ТЕСТОВОЕ УВЕДОМЛЕНИЕ!!11")

    except Exception as e:
        print(repr(e))


def userCurrentVideoIdInc(message, userCountryAccent):
    userId = message.from_user.id
    if userCountryAccent == "British":
        usersCollection.update_one({"id": str(userId)}, {"$inc": {"current_britain_video_id": 1}})
        print("Вроде обновил счетчик британского видео")
    elif userCountryAccent == "American":
        usersCollection.update_one({"id": str(userId)}, {"$inc": {"current_american_video_id": 1}})
        print("Вроде обновил счетчик американского видео")


def userCurrentMakePhraseIdInc(message):
    userId = message.from_user.id
    print(userId)
    usersCollection.update_one({"id": str(userId)}, {"$inc": {"current_make_phrase_id": 1}})
    print("Вроде обновил счетчик фраз")


def videoListening(message, userCountryAccent):
    videoCountsByCountry = videoCollection.count_documents(filter={"country_accent": str(userCountryAccent)})

    if userCountryAccent == "British":
        userCurrentVideoId = usersCollection.find_one({"id": str(message.from_user.id)}).get("current_britain_video_id")
        print("user current british video id: " + str(userCurrentVideoId))
    else:
        userCurrentVideoId = usersCollection.find_one({"id": str(message.from_user.id)}).get(
            "current_american_video_id")
        print("user current american video id: " + str(userCurrentVideoId))

    print("Video counts " + str(videoCountsByCountry))
    randomVideoId = random.randint(1, videoCountsByCountry)

    print(userCountryAccent)

    if userCurrentVideoId <= videoCountsByCountry:
        videoDataDB = videoCollection.find_one(
            {"id": str(userCurrentVideoId), "country_accent": str(userCountryAccent)})
    else:
        videoDataDB = videoCollection.find_one({"id": str(randomVideoId), "country_accent": str(userCountryAccent)})

    videoFileId = videoDataDB.get("file_id")
    print(videoDataDB)
    videoAnswers = videoDataDB.get("answers")
    shuffle(videoAnswers)
    rightAnswer = videoDataDB.get("right_answer")
    # print(rightAnswer)
    # print(videoAnswers)
    videoListenMarkup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    # videoListenInlineMarkup = types.InlineKeyboardMarkup

    for i in range(0, 4):
        videoItem = types.KeyboardButton(chr(10102 + i) + " " + videoAnswers[i])
        if videoAnswers[i] == rightAnswer:
            rightAnswer = chr(10102 + i) + " " + rightAnswer
        videoListenMarkup.add(videoItem)

    video = types.Video(videoFileId, 1280, 720, duration=60)
    videoListenMarkup.add("Еще разговоров! 🤐", "На главную 🏠")

    bot.send_video(message.chat.id, video.file_id, reply_markup=videoListenMarkup)

    userAnswer = bot.send_chat_action(message.chat.id, "typing")

    return rightAnswer


def getWordTranslation(key: str) -> str:
    headers_auth = {'Authorization': 'Basic ' + config.ABBYY_KEY}
    auth = requests.post(URL_AUTH, headers=headers_auth)
    if auth.status_code == 200:
        token = auth.text
        headers_translate = {
            'Authorization': 'Bearer ' + token
        }
        # for i in range(1040, 1105):
        #     print(str(i) + ": " + chr(i))
        if ord(key[0]) in range(65, 91) or ord(key[0]) in range(97, 123):
            params = {
                'text': key,
                'srcLang': 1033,
                'dstLang': 1049,
                'isCaseSensitive': True,
            }
        elif ord(key[0]) in range(1040, 1104):
            params = {
                'text': key,
                'srcLang': 1049,
                'dstLang': 1033,
                'isCaseSensitive': True,
            }
        else:
            errMsg = "Простите, но я знаю перевод только с русского на английский и обратно"
            return errMsg
        req = requests.get(
            URL_TRANSLATE, headers=headers_translate, params=params)
        res = req.json()
        try:
            value = res['Translation']['Translation']
            return value
        except TypeError:
            if res == 'Incoming request rate exceeded for 50000 chars per day pricing tier':
                return res
            else:
                return None
    else:
        print('Error!' + str(auth.status_code))


if "HEROKU" in list(os.environ.keys()):
    # Для запуска на сервере
    @server.route('/' + config.TOKEN, methods=['POST'])
    def getMessage():
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return "!", 200


    @server.route("/")
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(url='https://englishtrainspoting.herokuapp.com/' + config.TOKEN)
        return "!", 200


    if __name__ == "__main__":
        server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)), debug=True)
else:
    # Для локального запуска
    bot.remove_webhook()
    bot.polling(none_stop=True)
