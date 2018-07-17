# -*- coding: utf-8 -*-

import secrets
import actions
import inline
import logging as log

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from common import get_partenza, day_to_string
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
                             text="Sei sicuro di voler confermare la tua rimozione dala"
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
            secrets.drivers[str(chat_id)] = str(secrets.users[str(chat_id)])
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
                         text="Inserisci l'ora di partenza nel formato HH:MM")
        actions.ReplyStatus.response_mode = 4
    elif data == "DELETE":
        direction, day = inline.separate_callback_data(update.callback_query.data)[2:4]
        # Creo una tastiera custom per Sì/No
        keyboard = []
        keyboard.append(InlineKeyboardButton(
            "Sì", callback_data=inline.create_callback_data("TRIPS", ["CONFIRMDELETION", direction, day])))
        keyboard.append(InlineKeyboardButton(
            "No", callback_data=inline.create_callback_data("TRIPS", ["QUIT"])))

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "CONFIRMDELETION":
        direction, day = inline.separate_callback_data(update.callback_query.data)[2:4]
        if direction == "Salita":
            del secrets.groups_morning[day][chat_id]
            del secrets.times_morning[day][chat_id]
            bot.send_message(chat_id=chat_id, text="Viaggio cancellato con successo.")
        elif direction == "Discesa":
            del secrets.groups_evening[day][chat_id]
            del secrets.times_evening[day][chat_id]
            bot.send_message(chat_id=chat_id, text="Viaggio cancellato con successo.")
    elif data == "QUIT":
        bot.send_message(chat_id=chat_id, text="Operazione annullata.")


def newtrip_handler(bot, update):
    data, time = inline.separate_callback_data(update.callback_query.data)[1:3]
    try:
        day = inline.separate_callback_data(update.callback_query.data)[3]
    except IndexError as ex:
        day = None

    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    if day is None and (data == "SALITA" or data == "DISCESA"):
        keyboard = []
        for i in range(0, 5, 1):
            keyboard.append(InlineKeyboardButton(
                day_to_string(i)[:2],
                callback_data=inline.create_callback_data("NEWTRIP", [data, time, day_to_string(i)])))
        bot.send_message(chat_id=chat_id,
                         text="Scegli la data del viaggio.",
                         reply_markup=InlineKeyboardMarkup([keyboard, [InlineKeyboardButton(
                             "Annulla", callback_data=inline.create_callback_data("TRIPS", ["QUIT"]))]]))
    elif day is not None and data == "SALITA":
        secrets.groups_morning[str(day)][str(chat_id)] = []
        secrets.times_morning[str(day)][str(chat_id)] = str(time)
        bot.send_message(chat_id=chat_id, text="Viaggio aggiunto con successo.")
    elif day is not None and data == "DISCESA":
        secrets.groups_evening[str(day)][str(chat_id)] = []
        secrets.times_evening[str(day)][str(chat_id)] = str(time)
        bot.send_message(chat_id=chat_id, text="Viaggio aggiunto con successo.")
    else:
        bot.send_message(chat_id=chat_id, text="Spiacente, si è verificato un errore. Riprova più tardi.")


def response_confirmtrip(bot, update):
    try:
        time = parser.parse(update.message.text)
    except ValueError as ex:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Formato non valido!")
        actions.ReplyStatus.response_mode = 0
        return
    if time.hour == 0:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Formato non valido!")
        actions.ReplyStatus.response_mode = 0
        return

    time = str(time.hour).zfill(2) + ":" + str(time.minute).zfill(2)

    keyboard = []
    keyboard.append(InlineKeyboardButton(
        "per Povo", callback_data=inline.create_callback_data("NEWTRIP", ["SALITA", time])))
    keyboard.append(InlineKeyboardButton(
        "per il NEST", callback_data=inline.create_callback_data("NEWTRIP", ["DISCESA", time])))

    bot.send_message(chat_id=update.message.chat_id,
                     text="Vuoi aggiungere un viaggio verso il NEST o Povo?",
                     reply_markup=InlineKeyboardMarkup([keyboard]))

    actions.ReplyStatus.response_mode = 0


def response_me_driver(bot, update):
    chat_id = update.message.chat_id
    if secrets.drivers[str(chat_id)] == str(update.message.text):

        del secrets.drivers[str(chat_id)]
        for i in secrets.groups_morning:
            if str(chat_id) in secrets.groups_morning[i]:
                del secrets.groups_morning[i][str(chat_id)]
        for i in secrets.groups_evening:
            if str(chat_id) in secrets.groups_evening[i]:
                del secrets.groups_evening[i][str(chat_id)]
        for i in secrets.times_morning:
            if str(chat_id) in secrets.times_morning[i]:
                del secrets.times_morning[i][str(chat_id)]
        for i in secrets.times_evening:
            if str(chat_id) in secrets.times_evening[i]:
                del secrets.times_evening[i][str(chat_id)]

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
    if str(update.message.chat_id).decode('utf-8') in secrets.drivers:
        string = "Smettere di essere un autista di UberNEST"
    else:
        string = "Diventare un autista di UberNEST"

    keyboard = []
    if str(update.message.chat_id).decode('utf-8') in secrets.drivers:
        keyboard.append([InlineKeyboardButton(
            "Gestire i miei viaggi", callback_data=inline.create_callback_data("ME", ["TRIPS"]))])
    keyboard.append([InlineKeyboardButton(
        string, callback_data=inline.create_callback_data("ME", ["DRIVER"]))])
    keyboard.append([InlineKeyboardButton(
        "Cancellarmi dal sistema di UberNEST", callback_data=inline.create_callback_data("ME", ["REMOVAL"]))])
    return InlineKeyboardMarkup(keyboard)


def trips_keyboard(update):
    user = str(update.callback_query.from_user.id)
    keyboard = []
    keyboard.append([InlineKeyboardButton(
        "Aggiungi un nuovo viaggio", callback_data=inline.create_callback_data("TRIPS", ["ADD"]))])

    for i in range(0, 5, 1):
        trip = get_partenza(user.decode('utf-8'), day_to_string(i), "Salita")
        if trip is not None:
            keyboard.append([InlineKeyboardButton(
                day_to_string(i) + ": " + trip, callback_data=inline.create_callback_data("TRIPS",
                                                                                          ["DELETE", "Salita",
                                                                                           day_to_string(i)]))])

        trip = get_partenza(user.decode('utf-8'), day_to_string(i), "Discesa")
        if trip is not None:
            keyboard.append([InlineKeyboardButton(
                day_to_string(i) + ": " + trip, callback_data=inline.create_callback_data("TRIPS",
                                                                                          ["DELETE", "Discesa",
                                                                                           day_to_string(i)]))])

    keyboard.append([InlineKeyboardButton("Esci", callback_data=inline.create_callback_data("TRIPS", ["QUIT"]))])
    return InlineKeyboardMarkup(keyboard)
