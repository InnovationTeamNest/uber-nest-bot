# -*- coding: utf-8 -*-

from lib.telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup

import actions
import secrets


def inline_handler(bot, update):  # TODO Expand inline functionality
    person, direction = separate_callback_data(update.callback_query.data)
    person = int(person)

    bot.send_chat_action(chat_id=update.callback_query.from_user.id, action=ChatAction.TYPING)
    update.callback_query.message.delete()

    if direction == "Salita":
        groups = secrets.groups_morning
    elif direction == "Discesa":
        groups = secrets.groups_evening
    else:
        groups = None

    if len(groups[person]) < 4:
        if update.callback_query.from_user.id == person:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Sei tu l'autista!")
        elif update.callback_query.from_user.id not in groups[person]:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Prenotato con " + secrets.users[person] + " con successo")
            groups[person].append(update.callback_query.from_user.id)
        else:
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Ti sei già prenotato con questa persona!")
    else:
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text="Posti per domani esauriti.")


def persone_keyboard():
    keyboard = []
    for i in secrets.groups_morning:
        keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + actions.get_partenza(i, "Salita"),
                                              callback_data=create_callback_data(i, "Salita"))])
    for i in secrets.groups_evening:
        keyboard.append([InlineKeyboardButton(secrets.users[i] + " - " + actions.get_partenza(i, "Discesa"),
                                              callback_data=create_callback_data(i, "Discesa"))])
    return InlineKeyboardMarkup(keyboard)


def create_callback_data(person, direction):
    """ Create the callback data associated to each button"""
    return ";".join([str(person), direction])


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(";")