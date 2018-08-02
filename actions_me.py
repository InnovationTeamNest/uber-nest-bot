# -*- coding: utf-8 -*-
import money
import secrets
import actions
import inline
import logging as log
import common

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from dateutil import parser


def me(bot, update):
    if str(update.message.chat_id) in secrets.users:
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
            keyboard = [InlineKeyboardButton("Sì", callback_data=inline.create_callback_data("ME", "DELETEDRIVER")),
                        InlineKeyboardButton("No", callback_data=inline.create_callback_data("CANCEL"))]
            bot.send_message(chat_id=chat_id,
                             text="Sei sicuro di voler confermare la tua rimozione dalla"
                                  " lista degli autisti? Se cambiassi idea, puoi sempre iscriverti"
                                  " di nuovo da /me. La cancellazione dal sistema comporterà il reset"
                                  " completo di tutte le prenotazioni.",
                             reply_markup=InlineKeyboardMarkup([keyboard]))
        else:
            keyboard = [InlineKeyboardButton("Sì", callback_data=inline.create_callback_data("ME", "SLOTSDRIVER")),
                        InlineKeyboardButton("No", callback_data=inline.create_callback_data("CANCEL"))]
            bot.send_message(chat_id=chat_id,
                             text="Una volta finalizzata l'iscrizione come autista, potrai gestire i tuoi"
                                  " viaggi direttamente da questo bot. Contatta un membro del direttivo di"
                                  " UberNEST per ulteriori informazioni.")
            bot.send_message(chat_id=chat_id,
                             text="Sei sicuro di voler diventare un autista di UberNEST?",
                             reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "MONEY":
        debits = money.get_debits(str(chat_id))
        if len(debits) != 0:
            string = ""
            for creditor in debits:
                string += secrets.users[str(creditor[0])] + " - " + str(creditor[1]) + " EUR\n"
            bot.send_message(chat_id=chat_id,
                             text="Al momento possiedi debiti verso le seguenti persone: \n" + string)

        if str(chat_id) in secrets.drivers:
            credits = money.get_credits(str(chat_id))
            if len(credits) != 0:
                string = ""
                for debitor in credits:
                    string += secrets.users[str(debitor[0])] + " - " + str(debitor[1]) + " EUR\n"
                bot.send_message(chat_id=chat_id,
                                 text="Al momento possiedi queste persone hanno debiti con te: \n" + string)
    elif data == "REMOVAL":
        keyboard = [InlineKeyboardButton("Sì", callback_data=inline.create_callback_data("ME", "CONFIRMREMOVAL")),
                    InlineKeyboardButton("No", callback_data=inline.create_callback_data("CANCEL"))]
        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler confermare la tua rimozione completa dal sistema?"
                              " L'operazione è reversibile, ma tutte le"
                              " tue prenotazioni e viaggi verranno cancellati.",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "SLOTSDRIVER":  # Supporto sensato da macchine con 2 posti fino a 5
        keyboard = [InlineKeyboardButton("1", callback_data=inline.create_callback_data("ME", "CONFIRMDRIVER", "1")),
                    InlineKeyboardButton("2", callback_data=inline.create_callback_data("ME", "CONFIRMDRIVER", "2")),
                    InlineKeyboardButton("3", callback_data=inline.create_callback_data("ME", "CONFIRMDRIVER", "3")),
                    InlineKeyboardButton("4", callback_data=inline.create_callback_data("ME", "CONFIRMDRIVER", "4")),
                    InlineKeyboardButton("5", callback_data=inline.create_callback_data("ME", "CONFIRMDRIVER", "5"))]
        bot.send_message(chat_id=chat_id,
                         text="Inserisci il numero di posti disponibili nella tua macchina (autista escluso!). "
                              "Al momento, non e' possibile modificare tale cifra; se necessario, "
                              "basta cancellarsi e reiscriversi come autista.",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "CONFIRMDRIVER":
        slots = int(inline.separate_callback_data(update.callback_query.data)[2])
        secrets.drivers[str(chat_id)] = {u"Slots": slots}
        bot.send_message(chat_id=chat_id,
                         text="Sei stato inserito nella lista degli autisti! Usa il menu /me per gestire"
                              " il tuo profilo autista.")
    elif data == "DELETEDRIVER":
        del secrets.drivers[str(chat_id)]

        for direction in secrets.groups:
            for day in secrets.groups[direction]:
                if str(chat_id) in secrets.groups[direction][day]:
                    del secrets.groups[direction][day][str(chat_id)]

        bot.send_message(chat_id=chat_id,
                         text="Sei stato rimosso con successo dall'elenco degli autisti.")
    elif data == "CONFIRMREMOVAL":
        del secrets.users[str(chat_id)]
        if str(chat_id) in secrets.drivers:
            del secrets.drivers[str(chat_id)]

            for direction in secrets.groups:
                for day in secrets.groups[direction]:
                    if str(chat_id) in secrets.groups[direction][day]:
                        del secrets.groups[direction][day][str(chat_id)]
        bot.send_message(chat_id=chat_id, text="Sei stato rimosso con successo dal sistema.")


def trips_handler(bot, update):
    data = inline.separate_callback_data(update.callback_query.data)[1]
    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    log.info("Mode entered: " + data)
    if data == "ADD":
        bot.send_message(chat_id=chat_id,
                         text="Inserisci l'ora di partenza nel formato HH:MM. Se la combinazione di data e ora"
                              " e' già presente, verrà sovrascritta.")
        actions.ReplyStatus.response_mode = 4
    elif data == "DELETE":
        direction, day = inline.separate_callback_data(update.callback_query.data)[2:4]

        keyboard = [InlineKeyboardButton("Sì", callback_data=inline.create_callback_data(
                        "TRIPS", "CONFIRMDELETION", direction, day)),
                    InlineKeyboardButton("No", callback_data=inline.create_callback_data("CANCEL"))]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "CONFIRMDELETION":
        direction, day = inline.separate_callback_data(update.callback_query.data)[2:4]
        del secrets.groups[direction][day][chat_id]
        bot.send_message(chat_id=chat_id, text="Viaggio cancellato con successo.")


def new_trip(bot, update):
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
                callback_data=inline.create_callback_data("NEWTRIP", data, time, common.day_to_string(i))))

        bot.send_message(chat_id=chat_id,
                         text="Scegli la data del viaggio.",
                         reply_markup=InlineKeyboardMarkup([keyboard, [InlineKeyboardButton(
                             "Annulla", callback_data=inline.create_callback_data("CANCEL"))]]))

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

    keyboard = [InlineKeyboardButton("per Povo",
                                     callback_data=inline.create_callback_data("NEWTRIP", "Salita", time)),
                InlineKeyboardButton("per il NEST",
                                     callback_data=inline.create_callback_data("NEWTRIP", "Discesa", time))]

    bot.send_message(chat_id=update.message.chat_id,
                     text="Vuoi aggiungere un viaggio verso il NEST o Povo?",
                     reply_markup=InlineKeyboardMarkup([keyboard]))

    actions.ReplyStatus.response_mode = 0


def me_keyboard(update):
    keyboard = []
    if str(update.message.chat_id) in secrets.drivers:
        driver_string = "Smettere di essere un autista di UberNEST"
        money_string = "Gestire i miei debiti e i miei crediti"
        keyboard.append([InlineKeyboardButton("Gestire i miei viaggi",
                                              callback_data=inline.create_callback_data("ME", "TRIPS"))])
    else:
        driver_string = "Diventare un autista di UberNEST"
        money_string = "Gestire i miei debiti"

    keyboard.append([InlineKeyboardButton(driver_string,
                                          callback_data=inline.create_callback_data("ME", "DRIVER"))])
    keyboard.append([InlineKeyboardButton(money_string,
                                          callback_data=inline.create_callback_data("ME", "MONEY"))])
    keyboard.append([InlineKeyboardButton("Cancellarmi dal sistema di UberNEST",
                                          callback_data=inline.create_callback_data("ME", "REMOVAL"))])
    keyboard.append([InlineKeyboardButton("Esci dal menu",
                                          callback_data=inline.create_callback_data("CANCEL"))])
    return InlineKeyboardMarkup(keyboard)


def trips_keyboard(update):
    user = str(update.callback_query.from_user.id)
    keyboard = [[InlineKeyboardButton(
        "Aggiungi un nuovo viaggio", callback_data=inline.create_callback_data("TRIPS", "ADD"))]]

    for direction in common.groups:
        for day in common.groups[direction]:
            trip = common.get_partenza(user.decode('utf-8'), day, direction)
            if trip is not None:
                keyboard.append([
                    InlineKeyboardButton(day + ": " + trip,
                                         callback_data=inline.create_callback_data("TRIPS", "DELETE", direction, day))])

    keyboard.append([InlineKeyboardButton("Esci", callback_data=inline.create_callback_data("CANCEL"))])
    return InlineKeyboardMarkup(keyboard)
