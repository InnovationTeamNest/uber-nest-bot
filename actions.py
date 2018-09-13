# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from telegram import InlineKeyboardButton, ChatAction, InlineKeyboardMarkup

import common
import inline
import secret_data


class ReplyStatus:
    response_mode = 0


def text_filter(bot, update):
    if ReplyStatus.response_mode == 0:
        bot.send_message(chat_id=update.message.chat_id, text="Digita /help per avere informazioni sui comandi.")
    elif ReplyStatus.response_mode == 1:
        response_registra(bot, update)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Benvenuto nel bot di UberNEST. Per iniziare, digita /registra per registrarti a sistema, "
                          + "o /help per visualizzare i comandi.")


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Comandi disponibili:")

    text = "/me - Gestisci il tuo profilo.\n/prenota - Gestisci le prenotazioni." \
        if str(update.message.chat_id) in secret_data.users else \
        "/registra - Aggiungi il tuo nome al database."

    text = text + "\n\n/oggi - Visualizza le prenotazioni per oggi." \
                + "\n/domani - Visualizza le prenotazioni per domani." \
                + "\n/settimana - Visualizza le prenotazioni per la settimana."

    bot.send_message(chat_id=update.message.chat_id, text=text)


def oggi(bot, update):
    fetch_bookings(bot, update.message.chat_id, common.today())


def domani(bot, update):
    fetch_bookings(bot, update.message.chat_id, common.tomorrow())


def lunedi(bot, update):
    fetch_bookings(bot, update.message.chat_id, "Lunedì")


def martedi(bot, update):
    fetch_bookings(bot, update.message.chat_id, "Martedì")


def mercoledi(bot, update):
    fetch_bookings(bot, update.message.chat_id, "Mercoledì")


def giovedi(bot, update):
    fetch_bookings(bot, update.message.chat_id, "Giovedì")


def venerdi(bot, update):
    fetch_bookings(bot, update.message.chat_id, "Venerdì")


def settimana(bot, update):
    keyboard = []

    for i in range(0, 5, 1):
        day = common.day_to_string(i)
        keyboard.append(
            InlineKeyboardButton(day[:2], callback_data=inline.create_callback_data("SHOWBOOKINGS", day)))

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

        for direction in secret_data.groups:
            day_group = secret_data.groups[direction][day]  # Rappresenta l'insieme di trip per coppia direzione/giorno
            if len(day_group) > 0:  # Caso in cui c'è qualcuno che effettivamente farà un viaggio
                header = "Viaggi " + common.direction_to_name(direction) + ": \n\n"
                messages = []

                for driver in day_group:  # Stringhe separate per ogni autista
                    people = [secret_data.users[user]["Name"] for mode in day_group[driver]
                              if mode == "Temporary" or mode == "Permanent" for user in day_group[driver][mode]]
                    # Aggiungo ogni viaggio trovato alla lista
                    messages.append(secret_data.users[driver]["Name"] + " - " +
                                    day_group[driver]["Time"] + ":\n" + ", ".join(people))

                bot.send_message(chat_id=chat_id, text=header + "\n".join(messages))
            else:
                bot.send_message(chat_id=chat_id,
                                 text="Nessuna persona in viaggio " + common.direction_to_name(direction) + " oggi.")

    else:
        bot.send_message(chat_id=chat_id, text=day + " UberNEST non sarà attivo.")


def registra(bot, update):
    if str(update.message.chat_id) in secret_data.users:
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
    secret_data.users[str(update.message.chat_id)] = {"Name": str(user), "Debit": {}}
    bot.send_message(chat_id=update.message.chat_id,
                     text="Il tuo username è stato aggiunto con successo"
                          " al database. Usa i seguenti comandi:\n/me "
                          "per gestire il tuo profilo, gestire i debiti e "
                          "i crediti e diventare autista di UberNEST.\n"
                          "/prenota per effettuare e disdire prenotazioni.")
    ReplyStatus.response_mode = 0
