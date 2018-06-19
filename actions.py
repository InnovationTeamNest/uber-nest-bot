# -*- coding: utf-8 -*-

import logging as log
import secrets
from inline import persone_keyboard


def turni(bot, update):
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


def emergenza(bot, update):
    pass


def registra(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="Disclaimer sul regolamento etc..."
                          "contatta Paolo prima di iscriverti pls")
    bot.send_message(chat_id=update.message.chat_id,
                     text="To be implemented")


def get_partenza(person, time):
    if time == "Salita":
        return secrets.times_morning[person] + " ➡ Povo"
    elif time == "Discesa":
        return secrets.times_evening[person] + " ⬅ Nest"
    else:
        return None


