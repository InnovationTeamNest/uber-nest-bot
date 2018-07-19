# -*- coding: utf-8 -*-

import common
import secrets
import actions_me
import inline

from common import tomorrow, today, day_to_string
from lib.telegram import InlineKeyboardButton, ChatAction


class ReplyStatus:
    response_mode = 0

    def __init__(self):
        pass

    @staticmethod
    def allfalse():
        ReplyStatus.response_mode = 0


def text_filter(bot, update):
    if ReplyStatus.response_mode == 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Digita /help per avere informazioni sui comandi.")
    elif ReplyStatus.response_mode == 1:
        response_registra(bot, update)
    elif ReplyStatus.response_mode == 2:
        actions_me.response_me_driver(bot, update)
    elif ReplyStatus.response_mode == 3:
        actions_me.response_me_user(bot, update)
    elif ReplyStatus.response_mode == 4:
        actions_me.response_confirmtrip(bot, update)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Benvenuto nel bot di UberNEST. Per iniziare,"
                          " digita /help per visualizzare i comandi.")


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Comandi disponibili:")

    if str(update.message.chat_id).decode('utf-8') in secrets.users:
        text = "/me - Gestisci il tuo profilo." \
               + "\n/prenota - Gestisci le prenotazioni."
    else:
        text = "/registra - Aggiungi il tuo nome al database."

    text = text + "\n\n/oggi - Visualizza le prenotazioni per oggi." \
                + "\n/domani - Visualizza le prenotazioni per domani." \
                + "\n/settimana - Visualizza le prenotazioni per la settimana."

    bot.send_message(chat_id=update.message.chat_id, text=text)


def oggi(bot, update):
    fetch_bookings(bot, update.message.chat_id, today())


def domani(bot, update):
    fetch_bookings(bot, update.message.chat_id, tomorrow())


def settimana(bot, update):
    keyboard = []

    for i in range(0, 5, 1):
        keyboard.append(InlineKeyboardButton(
            day_to_string(i)[:2],
            callback_data=inline.create_callback_data("SHOWBOOKINGS", [day_to_string(i)])))

    bot.send_message(chat_id=update.message.chat_id, text="Scegli il giorno di cui visualizzare le prenotazioni",
                     reply_markup=[keyboard])


def show_bookings(bot, update):
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    data = inline.separate_callback_data(update.callback_query.data)
    fetch_bookings(bot, chat_id, data[1])


def fetch_bookings(bot, chat_id, day):
    if common.is_weekday(day):
        bot.send_message(chat_id=chat_id,
                         text="Lista delle prenotazioni per "
                              + day.lower() + ": ")

        groups = secrets.groups_morning[day]
        if len(groups) > 0:
            message = "Persone in salita: \n\n"
            for day in groups:
                people = [secrets.users[user] for day in groups for mode in groups[day]
                          if mode != u"Time" for user in groups[day][mode]]
                bot.send_message(chat_id=chat_id,
                                 text=message + secrets.users[day] + ":\n" + ", ".join(people))

        groups = secrets.groups_evening[day]
        if len(groups) > 0:
            message = "Persone in discesa: \n\n"
            for day in groups:
                people = [secrets.users[user] for day in groups for mode in groups[day]
                          if mode != u"Time" for user in groups[day][mode]]
                bot.send_message(chat_id=chat_id,
                                 text=message + secrets.users[day] + ":\n" + ", ".join(people))

    else:
        bot.send_message(chat_id=chat_id,
                         text=day + " UberNEST non sarà attivo.")


def registra(bot, update):
    if str(update.message.chat_id).decode('utf-8') in secrets.users:
        bot.send_message(chat_id=update.message.chat_id, text="Questo utente risulta già iscritto a sistema!")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="In seguito all'iscrizione, assicurati di unirti "
                              "al gruppo UberNEST, e di aver letto ed accettato "
                              "il regolamento in tutti i suoi punti. Per ulteriori"
                              " informazioni, contatta un membro del direttivo di "
                              "UberNEST (Filippo Spaggiari, Paolo Teta).")
        bot.send_message(chat_id=update.message.chat_id,
                         text="Inserire nome e cognome, che verranno mostrati"
                              " sia agli autisti sia ai passeggeri. Ogni violazione di"
                              " queste regole verrà punita con la rimozione dal"
                              " sistema.")
        ReplyStatus.response_mode = 1


def response_registra(bot, update):
    user = update.message.text
    secrets.users[str(update.message.chat_id)] = str(user)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Il tuo username è stato aggiunto con successo"
                          " al Database. Usa il comando /me per gestire il tuo profilo.")
    ReplyStatus.response_mode = 0
