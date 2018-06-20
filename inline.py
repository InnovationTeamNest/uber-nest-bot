# -*- coding: utf-8 -*-
import secrets

from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup
from dumpable import get_data, dump_data


def inline_handler(bot, update):  # TODO Expand inline functionality
    person, direction = separate_callback_data(update.callback_query.data)
    person = str(person).decode('utf-8')

    bot.send_chat_action(chat_id=update.callback_query.from_user.id,
                         action=ChatAction.TYPING)
    update.callback_query.message.delete()

    if direction == "Salita":
        groups = secrets.groups_morning
    elif direction == "Discesa":
        groups = secrets.groups_evening
    else:
        groups = None

    if len(groups[person]) < 4:
        if str(update.callback_query.from_user.id).decode('utf-8') == person:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Sei tu l'autista!")
        elif str(update.callback_query.from_user.id).decode('utf-8') not in groups[person]:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Prenotato con " + secrets.users[person] + " con successo")
            groups[person].append(str(update.callback_query.from_user.id).decode('utf-8'))
        else:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Ti sei già prenotato con questa persona!")
    else:
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text="Posti per domani esauriti.")


def persone_keyboard():
    keyboard = []
    for i in secrets.groups_morning:
        keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, "Salita"),
                                              callback_data=create_callback_data(i, "Salita"))])
    for i in secrets.groups_evening:
        keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + get_partenza(i, "Discesa"),
                                              callback_data=create_callback_data(i, "Discesa"))])
    return InlineKeyboardMarkup(keyboard)


def get_partenza(person, time):
    if time == "Salita":
        return str(secrets.times_morning[person].encode('utf-8') + " per Povo")
    elif time == "Discesa":
        return str(secrets.times_evening[person].encode('utf-8') + " per NEST")
    else:
        return None


def create_callback_data(person, direction):
    """ Create the callback data associated to each button"""
    return ";".join([str(person), direction])


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")