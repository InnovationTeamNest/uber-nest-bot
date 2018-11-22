# -*- coding: utf-8 -*-

import logging as log

import secrets
from commands.actions_show_bookings import fetch_bookings
from util import common
from util.filters import ReplyStatus


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

        if str(update.message.chat_id) in secrets.users:
            text.append("\n👤 /me - Gestisci il tuo profilo."
                        "\n📚 /prenota - Gestisci le tue prenotazioni."
                        "\n🚗 /parcheggio - Registra il tuo parcheggio di oggi."
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


# @Deprecated
def info(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Attenzione! Questo comando è stato deprecato"
                          " e verrà rimosso a partire dal 01/12/2018."
                          "\nControlla le informazioni nella Bio.")


def oggi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), common.today())

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def domani(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), common.tomorrow())

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def lunedi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), "Lunedì")

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def martedi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), "Martedì")

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def mercoledi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), "Mercoledì")

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def giovedi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), "Giovedì")

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


def venerdi(bot, update):
    message, keyboard = fetch_bookings(str(update.message.chat_id), "Venerdì")

    bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=keyboard, parse_mode="Markdown")


# @Deprecated
def settimana(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Attenzione! Questo comando è stato deprecato"
                          " e verrà rimosso a partire dal 01/12/2018."
                          "\nUsa /oggi, /domani oppure / seguito da un"
                          " giorno qualsiasi e naviga con i comandi presenti.")


def registra(bot, update):
    if str(update.message.chat_id) in secrets.users:
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
                              " queste regole verrà punita con la rimo<zione dal"
                              " sistema.")
        ReplyStatus.response_mode = 1


def response_registra(bot, update):
    user = update.message.text
    secrets.users[str(update.message.chat_id)] = {"Name": str(user), "Debit": {}}
    bot.send_message(chat_id=update.message.chat_id,
                     text="Il tuo username è stato aggiunto con successo"
                          " al database. Usa i seguenti comandi:"
                          "\n\n/me per gestire il tuo profilo, gestire i debiti"
                          " e i crediti e diventare autista di UberNEST."
                          "\n/prenota per effettuare e disdire prenotazioni.")
    log.info(f"Nuovo utente iscritto: {user}")
    ReplyStatus.response_mode = 0
