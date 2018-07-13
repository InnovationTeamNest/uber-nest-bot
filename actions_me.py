# -*- coding: utf-8 -*-
import secrets
import actions
import inline
import logging as log
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction


def me(bot, update):
    if str(update.message.chat_id).decode('utf-8') in secrets.users:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Cosa vuoi fare?",
                         reply_markup=me_keyboard(update))


def me_handler(bot, update):
    data = inline.separate_callback_data(update.callback_query.data)[1]

    bot.send_chat_action(chat_id=update.callback_query.from_user.id,
                         action=ChatAction.TYPING)
    update.callback_query.message.delete()

    log.info("Mode entered: " + data)

    if data == "TRIPS":
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text="Funzionalità ancora non implementata")
    elif data == "DRIVER":
        if str(update.callback_query.from_user.id).decode('utf-8') in secrets.drivers:
            # Caso dell'utente presente a sistema
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Sei sicuro di voler confermare la tua rimozione dalla"
                                  " lista degli autisti? Se cambiassi idea, puoi sempre iscriverti"
                                  " di nuovo da /me. La cancellazione dal sistema comporterà il reset"
                                  " completo di tutte le prenotazioni.")
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Se sei sicuro, scrivi come messaggio il tuo nome e cognome esattamente"
                                  " come l'hai inserito a sistema.")
            actions.ReplyStatus.response_mode = 2
        else:
            # Utente non presente
            bot.send_message(chat_id=update.callback_query.from_user.id,
                             text="Contatta un membro del direttivo per ulteriori informazioni "
                                  "al riguardo. ---DISCLAIMER DEL REGOLAMENTO  --- al momento l'utente"
                                  " è aggiunto in ogni caso")
        secrets.drivers[str(update.callback_query.from_user.id)] = str(
            secrets.users[str(update.callback_query.from_user.id)])
    elif data == "REMOVAL":
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text="Sei sicuro di voler confermare la tua rimozione completa dal sistema? "
                              " L'operazione è reversibile, ma tutte le tue prenotazioni e viaggi verranno cancellati. ")
        bot.send_message(chat_id=update.callback_query.from_user.id,
                         text="Se sei sicuro, scrivi come messaggio il tuo nome e cognome esattamente"
                              " come l'hai inserito a sistema.")
        actions.ReplyStatus.response_mode = 3


def response_me_driver(bot, update):
    chat_id = update.message.chat_id
    if secrets.drivers[str(chat_id)] == str(update.message.text):

        del secrets.drivers[str(chat_id)]
        for i in secrets.groups_morning:
            if str(chat_id) in secrets.groups_morning[i]:
                del secrets.groups_morning[i][str(chat_id)]
        for i in secrets.groups_evening:
            if str(chat_id) in secrets.groups_evening[i]:
                del secrets.groups_evening[i][str(chat_id)]
        for i in secrets.times_morning:
            if str(chat_id) in secrets.times_morning[i]:
                del secrets.times_morning[i][str(chat_id)]
        for i in secrets.times_evening:
            if str(chat_id) in secrets.times_evening[i]:
                del secrets.times_evening[i][str(chat_id)]

        bot.send_message(chat_id=update.message.chat_id,
                         text="Sei stato rimosso con successo dall'elenco degli autisti.")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Cancellazione interrotta.")
    actions.ReplyStatus.response_mode = 0


def response_me_user(bot, update):
    chat_id = update.message.chat_id
    if secrets.users[str(chat_id)] == str(update.message.text):
        del secrets.users[str(chat_id)]

        bot.send_message(chat_id=update.message.chat_id,
                         text="Sei stato rimosso con successo dal sistema.")
    else:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Cancellazione interrotta.")
    actions.ReplyStatus.response_mode = 0


def me_keyboard(update):
    if str(update.message.chat_id).decode('utf-8') in secrets.drivers:
        string = "Smettere di essere un autista di UberNEST"
    else:
        string = "Diventare un autista di UberNEST"

    keyboard = []
    keyboard.append([InlineKeyboardButton("Gestire i miei viaggi",
                                          callback_data=inline.create_callback_data("ME", ["TRIPS"]))])
    keyboard.append([InlineKeyboardButton(string,
                                          callback_data=inline.create_callback_data("ME", ["DRIVER"]))])
    keyboard.append([InlineKeyboardButton("Cancellarmi dal sistema di UberNEST",
                                          callback_data=inline.create_callback_data("ME", ["REMOVAL"]))])
    return InlineKeyboardMarkup(keyboard)
