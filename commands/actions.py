# -*- coding: utf-8 -*-

import logging as log

from commands.actions_show_bookings import fetch_bookings, fetch_sessione
from data.data_api import is_registered, add_user, delete_user
from data.secrets import owner_id
from routing.filters import ReplyStatus
from util import common


#
# In questo file sono contenuti i comandi esclusivamente listati in /help e che comunque non supportano chiamate
# da callback query (quindi /me, /parcheggio e /prenota sono esclusi)
#


def start(bot, update):
    if update.message.chat.type == "private":  # Solo nei messaggi privati!
        bot.send_message(chat_id=update.message.chat_id,
                         text="Benvenuto nel bot di UberNEST. 🚗🚗"
                              "\n\nPer iniziare, digita /registra per registrarti a sistema"
                              " (obbligatorio per effettuare prenotazioni) o /help per visualizzare i comandi.")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Per iniziare, scrivimi un messaggio privato su @ubernestbot.")


def help(bot, update):
    if update.message.chat.type == "private":
        text = ["Comandi disponibili:"]

        text.append("\n\nℹ /info - Visualizza informazioni sulla versione del Bot.")

        if is_registered(update.message.chat_id):
            text.append("\n👤 /me - Gestisci il tuo profilo."
                        "\n📚 /prenota - Gestisci le tue prenotazioni."
                        "\n🚗 /parcheggio - Registra il tuo parcheggio di oggi.")

            if common.sessione:
                text.append("\n🗓 /oggi - Visualizza i viaggi disponibili.")
            else:
                text.append(
                    "\n\n🗓 /oggi - Visualizza le prenotazioni per oggi."
                    "\n🗓 /domani - Visualizza le prenotazioni per domani."
                    "\n\n📅 /lunedi - /martedi - /mercoledi"
                    "\n/giovedi - /venerdi - Visualizza le prenotazioni dei singoli giorni.")
        else:
            text.append("\n🖊 /registra - Inizia a usare UberNEST registrandoti al sistema.")

        bot.send_message(chat_id=update.message.chat_id, text="".join(text))
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Per informazioni, scrivimi /help in privato su @ubernestbot.")


def oggi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), common.today()) if not common.sessione \
        else fetch_sessione()

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def domani(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), common.tomorrow()) if not common.sessione \
        else fetch_sessione()

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def lunedi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), "Lunedì") if not common.sessione \
        else fetch_sessione()

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def martedi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), "Martedì") if not common.sessione \
        else fetch_sessione()

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def mercoledi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), "Mercoledì") if not common.sessione \
        else fetch_sessione()

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def giovedi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), "Giovedì") if not common.sessione \
        else fetch_sessione()

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def venerdi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), "Venerdì") if not common.sessione \
        else fetch_sessione()

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def registra(bot, update):
    if is_registered(update.message.chat_id):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Questo utente risulta già iscritto a sistema!")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="In seguito all'iscrizione, assicurati di unirti"
                              " al gruppo UberNEST, e di aver letto ed accettato"
                              " il regolamento in tutti i suoi punti. Per ulteriori"
                              " informazioni, contatta un membro del direttivo di"
                              " UberNEST.")
        bot.send_message(chat_id=update.message.chat_id,
                         text="Inserire nome e cognome, che verranno mostrati"
                              " sia agli autisti sia ai passeggeri. Ogni violazione di"
                              " queste regole verrà punita con la rimozione dal"
                              " sistema.")
        ReplyStatus.response_mode = 1


def response_registra(bot, update):
    user = update.message.text
    add_user(update.message.chat_id, user)
    bot.send_message(chat_id=update.message.chat_id,
                     text="Il tuo username è stato aggiunto con successo"
                          " al database. Usa i seguenti comandi:"
                          "\n\n/me per gestire il tuo profilo, gestire i debiti"
                          " e i crediti e diventare autista di UberNEST."
                          "\n/prenota per effettuare e disdire prenotazioni.")
    bot.send_message(chat_id=owner_id,
                     text=f"Nuovo utente iscritto a sistema: {user} con"
                          f" chat_id {update.message.chat_id}")
    log.info(f"Nuovo utente iscritto: {user}")
    ReplyStatus.response_mode = 0


def ban_user(bot, update, args):
    if update.message.chat_id == owner_id:
        user = args[0]
        delete_user(user)
        bot.send_message(chat_id=user, text="Sei stato bannato da UberNEST Bot.")
