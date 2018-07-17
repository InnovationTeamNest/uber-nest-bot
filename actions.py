# -*- coding: utf-8 -*-

import secrets
from actions_booking import fetch_bookings
from actions_me import response_me_driver, response_me_user, response_confirmtrip
from common import tomorrow, today


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
        response_me_driver(bot, update)
    elif ReplyStatus.response_mode == 3:
        response_me_user(bot, update)
    elif ReplyStatus.response_mode == 4:
        response_confirmtrip(bot, update)


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Benvenuto nel bot di UberNEST. Per iniziare,"
                          " digita /help per visualizzare i comandi.")


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Comandi disponibili:")

    text = "/oggi - Visualizza le prenotazioni per oggi.\n" \
           + "/domani - Visualizza le prenotazioni per domani.\n" \
           + "/settimana - Visualizza le prenotazioni per la settimana.\n\n" \
           + "/prenota - Effettua una prenotazione.\n" \
           + "/registra - Aggiungi il tuo nome al database."

    if str(update.message.chat_id).decode('utf-8') in secrets.users:
        text += "\n\n/me - Gestisci il tuo profilo."

    bot.send_message(chat_id=update.message.chat_id,
                     text=text)


def oggi(bot, update):
    fetch_bookings(bot, update, today())


def domani(bot, update):
    fetch_bookings(bot, update, tomorrow())


def settimana(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Feature non ancora implementata.")


def registra(bot, update):
    if str(update.message.chat_id).decode('utf-8') in secrets.users:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Questo utente risulta già iscritto a sistema!")
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
