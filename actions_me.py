# -*- coding: utf-8 -*-
from money.currency import Currency
from money.money import Money

import secrets
import actions
import inline
import logging as log
import common

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from dateutil import parser


def me(bot, update):
    if str(update.message.chat_id).decode('utf-8') in secrets.users:
        bot.send_message(chat_id=update.message.chat_id, text="Cosa vuoi fare?", reply_markup=me_keyboard(update))


def me_handler(bot, update):
    data = inline.separate_callback_data(update.callback_query.data)[1]
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    log.info("Mode entered: " + data)

    if data == "TRIPS":
        # Visualizza i vari trips dell'utente
        bot.send_message(chat_id=chat_id,
                         text="Viaggi (clicca su un viaggio per rimuoverlo):",
                         reply_markup=trips_keyboard(update))
    elif data == "DRIVER":
        if str(chat_id).decode('utf-8') in secrets.drivers:
            # Caso dell'utente presente a sistema
            bot.send_message(chat_id=chat_id,
                             text="Sei sicuro di voler confermare la tua rimozione dalla"
                                  " lista degli autisti? Se cambiassi idea, puoi sempre iscriverti"
                                  " di nuovo da /me. La cancellazione dal sistema comporterà il reset"
                                  " completo di tutte le prenotazioni.")
            bot.send_message(chat_id=chat_id,
                             text="Se sei sicuro, scrivi come messaggio il tuo nome e cognome esattamente"
                                  " come l'hai inserito a sistema.")
            actions.ReplyStatus.response_mode = 2
        else:
            # Utente non presente
            bot.send_message(chat_id=chat_id,
                             text="Contatta un membro del direttivo per ulteriori informazioni"
                                  " al riguardo. ---DISCLAIMER DEL REGOLAMENTO  --- al momento l'utente"
                                  " è aggiunto in ogni caso")
            secrets.drivers[str(chat_id)] = {
                u"Name": str(secrets.users[str(chat_id)]),
                u"Slots": 5,
                u"Credit": Money("0.00", Currency.EUR).format('it_IT')
            }
    elif data == "REMOVAL":
        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler confermare la tua rimozione completa dal sistema?"
                              " L'operazione è reversibile, ma tutte le"
                              " tue prenotazioni e viaggi verranno cancellati.")
        bot.send_message(chat_id=chat_id,
                         text="Se sei sicuro, scrivi come messaggio il tuo nome e cognome esattamente"
                              " come l'hai inserito a sistema.")
        actions.ReplyStatus.response_mode = 3


def trips_handler(bot, update):
    data = inline.separate_callback_data(update.callback_query.data)[1]
    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    log.info("Mode entered: " + data)
    if data == "ADD":
        bot.send_message(chat_id=chat_id,
                         text="Reminder: Se la data e l'ora sono già presenti, verranno sovrascritte."
                              "Inserisci l'ora di partenza nel formato HH:MM.")
        actions.ReplyStatus.response_mode = 4
    elif data == "DELETE":
        direction, day = inline.separate_callback_data(update.callback_query.data)[2:4]
        # Creo una tastiera custom per Sì/No
        keyboard = [InlineKeyboardButton("Sì", callback_data=inline.create_callback_data(
            "TRIPS", ["CONFIRMDELETION", direction, day])),
                    InlineKeyboardButton("No", callback_data=inline.create_callback_data(
                        "TRIPS", ["QUIT"]))]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "CONFIRMDELETION":
        direction, day = inline.separate_callback_data(update.callback_query.data)[2:4]
        del secrets.groups[direction][day][chat_id]
        bot.send_message(chat_id=chat_id, text="Viaggio cancellato con successo.")
    elif data == "QUIT":
        bot.send_message(chat_id=chat_id, text="Operazione annullata.")


def newtrip_handler(bot, update):
    data, time = inline.separate_callback_data(update.callback_query.data)[1:3]
    try:
        day = inline.separate_callback_data(update.callback_query.data)[3]
    except IndexError:
        day = None

    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    if day is None and (data == "Salita" or data == "Discesa"):
        keyboard = []

        for i in range(0, 5, 1):
            keyboard.append(InlineKeyboardButton(
                common.day_to_string(i)[:2],
                callback_data=inline.create_callback_data("NEWTRIP", [data, time, common.day_to_string(i)])))

        bot.send_message(chat_id=chat_id,
                         text="Scegli la data del viaggio.",
                         reply_markup=InlineKeyboardMarkup([keyboard, [InlineKeyboardButton(
                             "Annulla", callback_data=inline.create_callback_data("TRIPS", ["QUIT"]))]]))

    elif day is not None and (data == "Salita" or data == "Discesa"):
        secrets.groups[data][str(day)][str(chat_id)] = {u"Time": str(time), u"Permanent": [], u"Temporary": []}
        bot.send_message(chat_id=chat_id, text="Viaggio aggiunto con successo.")
    else:
        bot.send_message(chat_id=chat_id, text="Spiacente, si è verificato un errore. Riprova più tardi.")


def response_confirmtrip(bot, update):
    try:
        time = parser.parse(update.message.text)
    except ValueError:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Formato non valido!")
        actions.ReplyStatus.response_mode = 0
        return

    time = str(time.hour).zfill(2) + ":" + str(time.minute).zfill(2)

    keyboard = [InlineKeyboardButton(
        "per Povo", callback_data=inline.create_callback_data("NEWTRIP", ["Salita", time])),
        InlineKeyboardButton(
            "per il NEST", callback_data=inline.create_callback_data("NEWTRIP", ["Discesa", time]))]

    bot.send_message(chat_id=update.message.chat_id,
                     text="Vuoi aggiungere un viaggio verso il NEST o Povo?",
                     reply_markup=InlineKeyboardMarkup([keyboard]))

    actions.ReplyStatus.response_mode = 0


def response_me_driver(bot, update):
    chat_id = update.message.chat_id
    if secrets.drivers[str(chat_id)][u"Name"] == str(update.message.text):
        del secrets.drivers[str(chat_id)]

        for direction in secrets.groups:
            for day in secrets.groups[direction]:
                if str(chat_id) in secrets.groups[direction][day]:
                    del secrets.groups[direction][day][str(chat_id)]

        bot.send_message(chat_id=update.message.chat_id,
                         text="Sei stato rimosso con successo dall'elenco degli autisti.")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Cancellazione interrotta.")
    actions.ReplyStatus.response_mode = 0


def response_me_user(bot, update):
    chat_id = update.message.chat_id
    if secrets.users[str(chat_id)] == str(update.message.text):
        del secrets.users[str(chat_id)]
        response_me_driver(bot, update)
        bot.send_message(chat_id=chat_id, text="Sei stato rimosso con successo dal sistema.")
    else:
        bot.send_message(chat_id=chat_id, text="Cancellazione interrotta.")
    actions.ReplyStatus.response_mode = 0


def me_keyboard(update):
    keyboard = []
    if str(update.message.chat_id).decode('utf-8') in secrets.drivers:
        string = "Smettere di essere un autista di UberNEST"
        keyboard.append([InlineKeyboardButton("Gestire i miei viaggi",
                                              callback_data=inline.create_callback_data("ME", ["TRIPS"]))])
    else:
        string = "Diventare un autista di UberNEST"

    keyboard.append([InlineKeyboardButton(string,
                                          callback_data=inline.create_callback_data("ME", ["DRIVER"]))])
    keyboard.append([InlineKeyboardButton("Cancellarmi dal sistema di UberNEST",
                                          callback_data=inline.create_callback_data("ME", ["REMOVAL"]))])
    return InlineKeyboardMarkup(keyboard)


def trips_keyboard(update):
    user = str(update.callback_query.from_user.id)
    keyboard = [[InlineKeyboardButton(
        "Aggiungi un nuovo viaggio", callback_data=inline.create_callback_data("TRIPS", ["ADD"]))]]

    for direction in common.groups:
        for day in common.groups[direction]:
            trip = common.get_partenza(user.decode('utf-8'), common.day_to_string(day), direction)
            if trip is not None:
                keyboard.append([InlineKeyboardButton(
                    common.day_to_string(day) + ": " + trip,
                    callback_data=inline.create_callback_data("TRIPS",
                                                              ["DELETE", direction, common.day_to_string(day)]))])

    keyboard.append([InlineKeyboardButton("Esci", callback_data=inline.create_callback_data("TRIPS", ["QUIT"]))])
    return InlineKeyboardMarkup(keyboard)
