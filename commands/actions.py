# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging as log

from telegram import InlineKeyboardButton, ChatAction, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
from util import common
from util.filters import ReplyStatus, create_callback_data, separate_callback_data


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Benvenuto nel bot di UberNEST. Per iniziare, digita /registra per registrarti a sistema"
                          " (obbligatorio per effettuare prenotazioni) o /help per visualizzare i comandi.")


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Comandi disponibili:")

    text = "/me - Gestisci il tuo profilo.\n/prenota - Gestisci le tue prenotazioni." \
        if str(update.message.chat_id) in secret_data.users else \
        "/registra - Inizia a usare UberNEST registrandoti a sistema."

    text = text + "\n\n/oggi - Visualizza le prenotazioni per oggi." \
           + "\n/domani - Visualizza le prenotazioni per domani." \
           + "\n/settimana - Visualizza le prenotazioni per la settimana." \
           + "\n\n/lunedi - /martedi - /mercoledi\n/giovedi - /venerdi - " \
           + "Visualizza le prenotazioni dei singoli giorni." \
           + "\n\n/info - Visualizza informazioni sulla versione del Bot."

    bot.send_message(chat_id=update.message.chat_id, text=text)


def info(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="UberNEST Bot v. 1.5 - sviluppata dal"
                          " NEST Innovation Team. Contatta @mfranzil per suggerimenti,"
                          " proposte, bug o per partecipare attivamente allo"
                          " sviluppo del bot.\n\nUberNEST è una piattaforma creata da"
                          " Paolo Teta e Filippo Spaggiari nel 2017 come forma di"
                          " car-sharing per gli studenti di Povo residenti al NEST.")


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

    for day in common.work_days:
        keyboard.append(
            InlineKeyboardButton(day[:2], callback_data=create_callback_data("SHOW_BOOKINGS", day)))

    bot.send_message(chat_id=update.message.chat_id,
                     text="Scegli il giorno di cui visualizzare le prenotazioni.",
                     reply_markup=InlineKeyboardMarkup([keyboard]))


def show_bookings(bot, update):
    chat_id = update.callback_query.from_user.id

    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        update.callback_query.message.delete()
    except BadRequest:
        log.info("Failed to delete previous message")

    data = separate_callback_data(update.callback_query.data)
    fetch_bookings(bot, chat_id, data[1])


def fetch_bookings(bot, chat_id, day):
    if common.is_weekday(day):
        text = "Lista dei viaggi di " + day.lower() + ":\n"

        for direction in secret_data.groups:
            day_group = secret_data.groups[direction][day]  # Rappresenta l'insieme di trip per coppia direzione/giorno
            if len(day_group) > 0:  # Caso in cui c'è qualcuno che effettivamente farà un viaggio
                text = text + "\n" + common.direction_to_name(direction) + ":\n\n"

                for driver in day_group:  # Stringhe separate per ogni autista
                    people = [secret_data.users[user]["Name"] for mode in day_group[driver]
                              if mode == "Temporary" or mode == "Permanent" for user in day_group[driver][mode]]
                    # Aggiungo ogni viaggio trovato alla lista
                    text = text + "🚗 " + secret_data.users[driver]["Name"] + " - 🕒 " \
                           + day_group[driver]["Time"] + ":\n👥 " + ", ".join(people) + "\n\n"
            else:
                text = text + "\n\nNessuna persona in viaggio " + common.direction_to_name(direction) + " oggi."

        if str(chat_id) in secret_data.users:
            # Permetto l'uso della tastiera solo ai registrati
            keyboard = [
                [InlineKeyboardButton("Prenota una tantum",
                                      callback_data=create_callback_data("BOOKING", "DAY_CUSTOM", "Temporary", day))],
                [InlineKeyboardButton("Prenota permanentemente",
                                      callback_data=create_callback_data("BOOKING", "DAY_CUSTOM", "Permanent", day))]
            ]
            bot.send_message(chat_id=chat_id, text=text,
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            bot.send_message(chat_id=chat_id, text=text)

    else:
        bot.send_message(chat_id=chat_id, text=day + " UberNEST non è attivo.")


def registra(bot, update):
    if str(update.message.chat_id) in secret_data.users:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Questo utente risulta già iscritto a sistema!")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="In seguito all'iscrizione, assicurati di unirti "
                              "al gruppo UberNEST, e di aver letto ed accettato "
                              "il regolamento in tutti i suoi punti. Per ulteriori"
                              " informazioni, contatta un membro del direttivo di "
                              "UberNEST.")
        bot.send_message(chat_id=update.message.chat_id,
                         text="Inserire nome e cognome, che verranno mostrati"
                              " sia agli autisti sia ai passeggeri. Ogni violazione di"
                              " queste regole verrà punita con la rimozione dal"
                              " sistema.")
        ReplyStatus.response_mode = 1


def response_registra(bot, update):
    user = update.message.text
    secret_data.users[unicode(update.message.chat_id)] = {"Name": unicode(user), "Debit": {}}
    bot.send_message(chat_id=update.message.chat_id,
                     text="Il tuo username è stato aggiunto con successo"
                          " al database. Usa i seguenti comandi:\n/me "
                          "per gestire il tuo profilo, gestire i debiti e "
                          "i crediti e diventare autista di UberNEST.\n"
                          "/prenota per effettuare e disdire prenotazioni.")
    bot.send_message(chat_id=secret_data.owner_id,
                     text="Nuovo utente iscritto: " + str(user.encode('utf8')))
    ReplyStatus.response_mode = 0
