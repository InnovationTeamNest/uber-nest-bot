# -*- coding: utf-8 -*-

import common
import secrets
import actions_me
import inline

from common import tomorrow, today, day_to_string
from telegram import InlineKeyboardButton, ChatAction, InlineKeyboardMarkup


class ReplyStatus:
    response_mode = 0


def text_filter(bot, update):
    if ReplyStatus.response_mode == 0:
        bot.send_message(chat_id=update.message.chat_id, text="Digita /help per avere informazioni sui comandi.")
    elif ReplyStatus.response_mode == 1:
        response_registra(bot, update)
    elif ReplyStatus.response_mode == 4:
        actions_me.response_confirmtrip(bot, update)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Benvenuto nel bot di UberNEST. Per iniziare,"
                                                          " digita /help per visualizzare i comandi.")


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Comandi disponibili:")

    if str(update.message.chat_id) in secrets.users:
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
        day = str(day_to_string(i))
        keyboard.append(InlineKeyboardButton(day[:2],
                                             callback_data=inline.create_callback_data("SHOWBOOKINGS", day)))

    bot.send_message(chat_id=update.message.chat_id, text="Scegli il giorno di cui visualizzare le prenotazioni. ",
                     reply_markup=InlineKeyboardMarkup([keyboard]))


def show_bookings(bot, update):
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    data = inline.separate_callback_data(update.callback_query.data)
    fetch_bookings(bot, chat_id, data[1])


def fetch_bookings(bot, chat_id, day):
    if common.is_weekday(day):
        bot.send_message(chat_id=chat_id, text="Lista delle prenotazioni per " + day.lower() + ": ")

        for direction in secrets.groups:
            day_group = secrets.groups[direction][day]
            if len(day_group) > 0:
                message = "Persone in " + direction.lower() + ": \n\n"
                for driver in day_group:
                    people = [secrets.users[user] for driver in day_group for mode in day_group[driver]
                              if mode != u"Time" for user in day_group[driver][mode]]
                    bot.send_message(chat_id=chat_id,
                                     text=message + secrets.users[driver] + ":\n" + ", ".join(people))
    else:
        bot.send_message(chat_id=chat_id, text=day + " UberNEST non sara' attivo.")


def registra(bot, update):
    if str(update.message.chat_id) in secrets.users:
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
