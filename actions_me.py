# -*- coding: utf-8 -*-
import money
import secrets
import inline
import logging as log
import common

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction


def me(bot, update):
    if str(update.message.chat_id) in secrets.users:
        bot.send_message(chat_id=update.message.chat_id, text="Cosa vuoi fare?", reply_markup=me_keyboard(update))


def me_handler(bot, update):
    data = inline.separate_callback_data(update.callback_query.data)[1]
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    log.debug("Mode entered: " + data)

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
                                  " UberNEST per ulteriori informazioni.\n\n"
                                  "Sei sicuro di voler diventare un autista di UberNEST?",
                             reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "MONEY":
        debits = money.get_debits(str(chat_id))
        if len(debits) != 0:
            string = ""
            for creditor in debits:
                string += secrets.users[str(creditor[0])]["Name"] + " - " + str(creditor[1]) + " EUR\n"
            message = "Al momento possiedi debiti verso le seguenti persone: \n" + string \
                      + "\nContattali per saldare i debiti."
        else:
            message = "Al momento sei a posto con i debiti."

        if str(chat_id) in secrets.drivers:
            credits = money.get_credits(str(chat_id))
            if len(credits) != 0:
                keyboard = []
                for debitor in credits:
                    keyboard.append([InlineKeyboardButton(
                        secrets.users[str(debitor[0])][u"Name"] + " - " + str(debitor[1]) + " EUR",
                        callback_data=inline.create_callback_data("EDITMONEY", "NONE", *debitor))])
                keyboard.append([InlineKeyboardButton("Esci", callback_data=inline.create_callback_data("CANCEL"))])
                bot.send_message(chat_id=chat_id,
                                 text=message + "\n\nAl momento possiedi queste persone hanno debiti con te. Clicca "
                                                "su uno per modificarne o azzerarne il debito:",
                                 reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                bot.send_message(chat_id=chat_id, text=message + "\n\nNessuno ti deve denaro al momento.")
        else:
            bot.send_message(chat_id=chat_id, text=message)
    elif data == "REMOVAL":
        keyboard = [InlineKeyboardButton("Sì", callback_data=inline.create_callback_data("ME", "CONFIRMREMOVAL")),
                    InlineKeyboardButton("No", callback_data=inline.create_callback_data("CANCEL"))]
        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler confermare la tua rimozione completa dal sistema?"
                              " L'operazione è reversibile, ma tutte le"
                              " tue prenotazioni e viaggi verranno cancellati per sempre.",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "SLOTSDRIVER":  # Supporto sensato da macchine con 2 posti fino a 5
        keyboard = [InlineKeyboardButton(str(i),
                                         callback_data=inline.create_callback_data("ME", "CONFIRMDRIVER", str(i)))
                    for i in xrange(1, 6, 1)]  # Inserisco 5 bottoni per i posti con la list comprehension
        bot.send_message(chat_id=chat_id,
                         text="Inserisci il numero di posti disponibili nella tua macchina, autista escluso.",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "CONFIRMDRIVER":
        slots = int(inline.separate_callback_data(update.callback_query.data)[2])
        if str(chat_id) in secrets.drivers:
            bot.send_message(chat_id=chat_id,
                             text="Numero di posti della vettura aggiornato con successo.")
        else:
            bot.send_message(chat_id=chat_id,
                             text="Sei stato inserito nella lista degli autisti! Usa il menu /me per gestire"
                                  " il tuo profilo autista.")
        secrets.drivers[str(chat_id)] = {u"Slots": slots}
    elif data == "DELETEDRIVER":
        common.delete_driver(chat_id)
        bot.send_message(chat_id=chat_id,
                         text="Sei stato rimosso con successo dall'elenco degli autisti.")
    elif data == "CONFIRMREMOVAL":
        del secrets.users[str(chat_id)]
        if str(chat_id) in secrets.drivers:
            common.delete_driver(chat_id)
        bot.send_message(chat_id=chat_id, text="Sei stato rimosso con successo dal sistema.")


def trips_handler(bot, update):
    data = inline.separate_callback_data(update.callback_query.data)[1]
    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    log.debug("Mode entered: " + data)
    if data == "ADD":
        keyboard = [
            [InlineKeyboardButton("per Povo", callback_data=inline.create_callback_data("NEWTRIP", "Salita")),
             InlineKeyboardButton("per il NEST", callback_data=inline.create_callback_data("NEWTRIP", "Discesa"))],
            [InlineKeyboardButton("Annulla", callback_data=inline.create_callback_data("CANCEL"))]
        ]
        bot.send_message(chat_id=chat_id, text="Vuoi aggiungere un viaggio verso il NEST o Povo?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "DELETE":
        direction, day = inline.separate_callback_data(update.callback_query.data)[2:4]

        keyboard = [InlineKeyboardButton("Sì", callback_data=inline.create_callback_data("TRIPS", "CONFIRMDELETION",
                                                                                         direction, day)),
                    InlineKeyboardButton("No", callback_data=inline.create_callback_data("CANCEL"))]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    elif data == "CONFIRMDELETION":
        direction, day = inline.separate_callback_data(update.callback_query.data)[2:4]
        del secrets.groups[direction][day][chat_id]
        bot.send_message(chat_id=chat_id, text="Viaggio cancellato con successo.")


def newtrip_handler(bot, update):
    data = inline.separate_callback_data(update.callback_query.data)[1:]
    chat_id = str(update.callback_query.from_user.id)

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    update.callback_query.message.delete()
    # NOTA BENE: (Python 2.7 non supporta argomenti di posizione dopo *)
    if len(data) == 1:
        keyboard = []

        for i in range(0, 5, 1):
            keyboard.append(InlineKeyboardButton(common.day_to_string(i)[:2],  # Ordine: giorno, direzione
                            callback_data=inline.create_callback_data("NEWTRIP", common.day_to_string(i), *data)))
        # Aggiungo il pulsante annulla
        keyboard = [keyboard, [InlineKeyboardButton("Annulla", callback_data=inline.create_callback_data("CANCEL"))]]

        bot.send_message(chat_id=chat_id, text="Scegli il giorno della settimana del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 2:
        keyboard = [  # Ordine: ora, giorno, direzione
            [InlineKeyboardButton(str(i), callback_data=inline.create_callback_data("NEWTRIP", str(i), *data))
             for i in xrange(7, 14, 1)],
            [InlineKeyboardButton(str(i), callback_data=inline.create_callback_data("NEWTRIP", str(i), *data))
             for i in xrange(14, 21, 1)],
            [InlineKeyboardButton("Annulla", callback_data=inline.create_callback_data("CANCEL"))]
        ]
        bot.send_message(chat_id=chat_id, text="Scegli l'ora di partenza del viaggio",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 3:
        keyboard = [  # Ordine: minuti, ora, giorno, direzione
            [InlineKeyboardButton(str(i), callback_data=inline.create_callback_data("NEWTRIP", str(i), *data))
             for i in xrange(0, 30, 5)],
            [InlineKeyboardButton(str(i), callback_data=inline.create_callback_data("NEWTRIP", str(i), *data))
             for i in xrange(30, 60, 5)],
            [InlineKeyboardButton("Annulla", callback_data=inline.create_callback_data("CANCEL"))]
        ]
        bot.send_message(chat_id=chat_id, text="Scegli i minuti di partenza del viaggio",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    elif len(data) == 4:
        minute, hour, day, direction = data
        time = hour.zfill(2) + ":" + minute.zfill(2)

        secrets.groups[direction][str(day)][str(chat_id)] = {u"Time": str(time), u"Permanent": [], u"Temporary": []}
        bot.send_message(chat_id=chat_id, text="Viaggio aggiunto con successo:" +
                                               "\n\nOrario: " + str(time) +
                                               "\nGiorno: " + str(day) +
                                               "\nDirezione: " + common.direction_to_name(direction))
    else:
        bot.send_message(chat_id=chat_id, text="Spiacente, si è verificato un errore. Riprova più tardi.")


def me_keyboard(update):
    keyboard = []
    if str(update.message.chat_id) in secrets.drivers:
        money_string = "Gestire i miei debiti e i miei crediti"
        driver_string = "Smettere di essere un autista di UberNEST"
        keyboard.append([InlineKeyboardButton("Gestire i miei viaggi",
                                              callback_data=inline.create_callback_data("ME", "TRIPS"))])
        keyboard.append([InlineKeyboardButton("Modificare il numero di posti",
                                              callback_data=inline.create_callback_data("ME", "SLOTSDRIVER"))])
    else:
        money_string = "Gestire i miei debiti"
        driver_string = "Diventare un autista di UberNEST"

    keyboard.append([InlineKeyboardButton(money_string,
                                          callback_data=inline.create_callback_data("ME", "MONEY"))])
    keyboard.append([InlineKeyboardButton(driver_string,
                                          callback_data=inline.create_callback_data("ME", "DRIVER"))])
    keyboard.append([InlineKeyboardButton("Cancellarmi dal sistema di UberNEST",
                                          callback_data=inline.create_callback_data("ME", "REMOVAL"))])
    keyboard.append([InlineKeyboardButton("Uscire dal menu",
                                          callback_data=inline.create_callback_data("CANCEL"))])
    return InlineKeyboardMarkup(keyboard)


def trips_keyboard(update):
    user = str(update.callback_query.from_user.id)
    keyboard = [[InlineKeyboardButton("Aggiungi un nuovo viaggio",
                                      callback_data=inline.create_callback_data("TRIPS", "ADD"))]]

    for direction in common.groups:
        for day in common.groups[direction]:
            trip = common.get_partenza(user.decode('utf-8'), day, direction)
            if trip is not None:
                keyboard.append([InlineKeyboardButton(day + ": " + trip, callback_data=inline.create_callback_data(
                    "TRIPS", "DELETE", direction, day))])

    keyboard.append([InlineKeyboardButton("Esci", callback_data=inline.create_callback_data("CANCEL"))])
    return InlineKeyboardMarkup(keyboard)
