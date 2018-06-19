# -*- coding: utf-8 -*-

import logging as log
import secrets
from inline import persone_keyboard


# TODO: Aggiungere tutti i try-catch, espandere ReplyStatus, trovare
# TODO: il modo di dumpare e visualizzare i dati delle persone
# TODO: magari con una classe ausiliaria in main.py e json.dumps

class ReplyStatus:  # Classe ausilaria, un quick fix per gestire tutti i tipi di risposte dei metodi
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


def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Benvenuto nel bot di UberNEST. Per iniziare,"
                          " digita /help per visualizzare i comandi.")


def help(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Comandi disponibili:")
    bot.send_message(chat_id=update.message.chat_id,
                     text="/status - Visualizza le prenotazioni correnti.\n"
                          "/prenota - Effettua una prenotazione.\n"
                          "/registra - Aggiungi il tuo nome al database.")


def status(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Lista dei turni per oggi: ")
    groups = secrets.groups_morning
    bot.send_message(chat_id=update.message.chat_id,
                     text="Persone in salita: ")

    for i in groups:
        people = []
        for k in groups[i]:
            people.append(secrets.users[k])
        bot.send_message(chat_id=update.message.chat_id,
                         text=secrets.users[i] + ":\n" + ", ".join(people))

    groups = secrets.groups_evening
    bot.send_message(chat_id=update.message.chat_id,
                     text="Persone in discesa: ")
    for i in groups:
        people = []
        for k in groups[i]:
            people.append(secrets.users[k])
        bot.send_message(chat_id=update.message.chat_id,
                         text=secrets.users[i] + ":\n" + ", ".join(people))


def prenota(bot, update):
    try:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Scegli una persona:",
                         reply_markup=persone_keyboard())
    except Exception as ex:
        log.error(ex.message)


def registra(bot, update):
    if update.message.chat_id in secrets.users:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Questo utente risulta già iscritto a sistema!")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                     text="Disclaimer sul regolamento etc...") # TODO Expand
        bot.send_message(chat_id=update.message.chat_id,
                         text="Inserire nome e cognome, che verranno mostrati"
                         " sia agli autisti sia ai passeggeri. Ogni violazione di"
                         " queste regole verrà punita con la rimozione dal"
                         " sistema.")


def response_registra(bot, update):
    user = update.message.text
    secrets.users[update.message.chat_id] = user
    bot.send_message(chat_id=update.message.chat_id,
                     text="Il tuo username è stato aggiunto con successo"
                          " al Database. Contatta un membro del Direttivo"
                          " se desideri diventare un autista di UberNest.")


def get_partenza(person, time):
    if time == "Salita":
        return secrets.times_morning[person] + " ➡ Povo"
    elif time == "Discesa":
        return secrets.times_evening[person] + " ⬅ Nest"
    else:
        return None
