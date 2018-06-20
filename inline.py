# -*- coding: utf-8 -*-
import datetime

import secrets

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup


def inline_handler(bot, update):  # TODO Expand inline functionality
    person, direction = separate_callback_data(update.callback_query.data)
    person = str(person).decode('utf-8')

    bot.send_chat_action(chat_id=update.callback_query.from_user.id,
                         action=ChatAction.TYPING)
    update.callback_query.message.delete()

    try:
        if direction == "Salita":
            groups = secrets.groups_morning[next_day()]
        elif direction == "Discesa":
            groups = secrets.groups_evening[next_day()]
        else:
            groups = None
    except KeyError as ex:
        pass

    if len(groups[person]) < 4:
        if str(update.callback_query.from_user.id).decode('utf-8') == person:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Sei tu l'autista!")
        elif str(update.callback_query.from_user.id).decode('utf-8') not in groups[person]:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Prenotato con " + secrets.users[person] + " per domani con successo.")
            groups[person].append(str(update.callback_query.from_user.id).decode('utf-8'))
        else:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Ti sei già prenotato per domani con questa persona!")
    else:
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text="Posti per domani esauriti.")


def persone_keyboard():
    keyboard = []
    for i in secrets.groups_morning[next_day()]:
        keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, "Salita"),
                                              callback_data=create_callback_data(i, "Salita"))])
    for i in secrets.groups_evening[next_day()]:
        keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, "Discesa"),
                                              callback_data=create_callback_data(i, "Discesa"))])
    return InlineKeyboardMarkup(keyboard)


def get_partenza(person, time):
    output = None
    try:
        if time == "Salita":
            output = str(secrets.times_morning[next_day()][person].encode('utf-8') + " per Povo")
        elif time == "Discesa":
            output = str(secrets.times_evening[next_day()][person].encode('utf-8') + " per NEST")
    except KeyError as ex:
        output = None
    return output


def create_callback_data(person, direction):
    """ Create the callback data associated to each button"""
    return ";".join([str(person), direction])


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")


def next_day():
    date = (datetime.datetime.today().weekday() + 1) % 7
    if date == 0:
        return u"Lunedi"
    elif date == 1:
        return u'Martedi'
    elif date == 2:
        return u"Mercoledi"
    elif date == 3:
        return u"Giovedi"
    elif date == 4:
        return u"Venerdi"
    elif date == 5:
        return u"Sabato"
    elif date == 6:
        return u"Domenica"
