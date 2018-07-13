# -*- coding: utf-8 -*-
import secrets
from actions import ReplyStatus
from inline import create_callback_data, separate_callback_data
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction


def me(bot, update):
    if str(update.message.chat_id).decode('utf-8') in secrets.users:
        bot.send_message(chat_id=update.message.chat_id,
                         text="Cosa vuoi fare?",
                         reply_markup=me_keyboard(update))


def me_handler(bot, update):
    data = separate_callback_data(update.callback_query.data)[1:]

    bot.send_chat_action(chat_id=update.callback_query.from_user.id,
                         action=ChatAction.TYPING)
    update.callback_query.message.delete()

    if data == "TRIPS":
        pass
    elif data == "DRIVER":
        bot.send_message(chat_id=update.message.chat_id,
                         text="Contatta un membro del direttivo per ulteriori informazioni "
                              "al riguardo. ---DISCLAIMER DEL REGOLAMENTO  --- al momento l'utente"
                              "aggiunto in ogni caso")
        secrets.drivers[str(update.message.chat_id)] = str(secrets.users[str(update.message.chat_id)])
    elif data == "REMOVAL":
        bot.send_message(chat_id=update.message.chat_id,
                         text="Sei sicuro di voler confermare la tua rimozione dalla"
                              " lista degli autisti? Se cambiassi idea, puoi sempre iscriverti"
                              " di nuovo da /me. La cancellazione dal sistema comporterà il reset"
                              " completo di tutte le prenotazioni.")
        bot.send_message(chat_id=update.message.chat_id,
                         text="Se sei sicuro, scrivi come messaggio il tuo nome e cognome esattamente"
                              " come l'hai inserito a sistema.")
        ReplyStatus.response_mode = 2


def response_me(bot, update):
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
    ReplyStatus.response_mode = 0


def me_keyboard(update):
    if str(update.message.chat_id).decode('utf-8') in secrets.drivers:
        string = "Diventare un autista di UberNEST"
    else:
        string = "Smettere di essere un autista di UberNEST"

    keyboard = []
    keyboard.append([InlineKeyboardButton("Gestire i miei viaggi",
                                          callback_data=create_callback_data("ME", ["TRIPS"]))])
    keyboard.append([InlineKeyboardButton(string,
                                          callback_data=create_callback_data("ME", ["DRIVER"]))])
    keyboard.append([InlineKeyboardButton("Cancellarmi dal sistema di UberNEST",
                                          callback_data=create_callback_data("ME", ["REMOVAL"]))])
    return InlineKeyboardMarkup(keyboard)
