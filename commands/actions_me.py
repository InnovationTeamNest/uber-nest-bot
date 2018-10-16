# -*- coding: utf-8 -*-
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
from util import common
from util.filters import create_callback_data as ccd, separate_callback_data
from util.keyboards import me_keyboard, trips_keyboard


def me(bot, update):
    if update.callback_query:
        chat_id = str(update.callback_query.from_user.id)
        try:
            update.callback_query.message.delete()
        except BadRequest:
            print("Failed to delete previous message", file=sys.stderr)
    else:
        chat_id = str(update.message.chat_id)

    if chat_id in secret_data.users:
        bot.send_message(chat_id=chat_id, text="Cosa vuoi fare?", reply_markup=me_keyboard(chat_id))


#
# Tutte le richieste inviate a questo metodo provengono dalla me_keyboard in keyboards.py.
# Da questo menù viene gestito per intero /me (al livello base), le rimozioni e aggiunte di autista,
# e le rimozioni degli utenti.
#
def me_handler(bot, update):
    action = separate_callback_data(update.callback_query.data)[1]
    chat_id = str(update.callback_query.from_user.id)

    #
    # Da questo menù viene invocata la keyboard in keyboards.py.
    #
    if action == "TRIPS":
        bot.send_message(chat_id=chat_id,
                         text="Viaggi (clicca su un viaggio per modificarlo):",
                         reply_markup=trips_keyboard(chat_id))
    #
    # Da questo menù è possibile iscriversi e disiscriversi dalla modalità autista.
    #
    elif action == "DRIVER":
        if chat_id in secret_data.drivers:
            keyboard = [
                [InlineKeyboardButton("Sì", callback_data=ccd("ME", "CO_DR_RE")),
                 InlineKeyboardButton("No", callback_data=ccd("ME_MENU"))]]
            bot.send_message(chat_id=chat_id,
                             text="Sei sicuro di voler confermare la tua rimozione dalla"
                                  " lista degli autisti? Se cambiassi idea, puoi sempre iscriverti"
                                  " di nuovo da /me. La cancellazione dal sistema comporterà il reset"
                                  " completo di tutti i viaggi, impostazioni e crediti.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [
                [InlineKeyboardButton("Sì", callback_data=ccd("ME", "ED_DR_SL")),
                 InlineKeyboardButton("No", callback_data=ccd("ME_MENU"))]]
            bot.send_message(chat_id=chat_id,
                             text="Una volta finalizzata l'iscrizione come autista, potrai gestire i tuoi"
                                  " viaggi direttamente da questo bot. Contatta un membro del direttivo di"
                                  " UberNEST per ulteriori informazioni.\n\n"
                                  "Sei sicuro di voler diventare un autista di UberNEST?",
                             reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # US_RE = USER_REMOVAL
    # Da questo menù è possibile attuare la cancellazione completa e totale di tutti i dati dell'utente.
    # Nulla rimarrà, a parte i debiti che verranno inoltrati ai rispettivi creditori.
    #
    elif action == "US_RE":
        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("ME", "CO_US_RE")),
             InlineKeyboardButton("No", callback_data=ccd("ME_MENU"))]]

        user_debits = secret_data.users[chat_id]["Debit"]
        debitors = ""
        for creditor in user_debits:
            debitors += secret_data.users[creditor]["Name"] + " - " + str(user_debits[creditor]) + " EUR"

        message_text = "Sei sicuro di voler confermare la tua rimozione completa dal sistema?" \
                       + " L'operazione è reversibile, ma tutte le" \
                       + " tue prenotazioni e viaggi verranno cancellati per sempre."

        if debitors != "":
            message_text += "\n\nATTENZIONE! Hai debiti con le seguenti persone," \
                            " in caso di cancellazione dal sistema" \
                            " verranno avvisate dei tuoi debiti non saldati!\n" + debitors

        bot.send_message(chat_id=chat_id, text=message_text, reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # ED_DR_SL = EDIT_DRIVER_SLOTS
    # Questo menù permette di modificare gli slot a disposizione del guidatore.
    #
    elif action == "ED_DR_SL":
        # Inserisco 5 bottoni per i posti con la list comprehension
        keyboard = [[InlineKeyboardButton(str(i), callback_data=ccd("ME", "CO_DR", str(i)))
                     for i in range(1, 6, 1)],
                    [InlineKeyboardButton("Indietro", callback_data=ccd("ME_MENU"))],
                    [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]]
        bot.send_message(chat_id=chat_id,
                         text="Inserisci il numero di posti disponibili nella tua macchina, autista escluso.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # CO_DR = CONFIRM_DRIVER
    # Questo metodo svolge due diverse funzioni: se l'utente è un autista, è l'endpoint per la conferma
    # degli slot, altrimenti dell'iscrizione
    #
    elif action == "CO_DR":
        slots = int(separate_callback_data(update.callback_query.data)[2])
        if chat_id in secret_data.drivers:
            bot.send_message(chat_id=chat_id,
                             text="Numero di posti della vettura aggiornato con successo.")
        else:
            secret_data.drivers[chat_id] = {"Slots": slots}
            bot.send_message(chat_id=chat_id,
                             text="Sei stato inserito nella lista degli autisti! Usa il menu /me per aggiungere"
                                  " viaggi, modificare i posti auto, aggiungere un messaggio da mostrare ai tuoi"
                                  " passeggeri ed altro.")
    #
    # CO_DR_RE = CONFIRM_DRIVER_REMOVAL
    # Metodo di conferma della rimozione di un autista, vedi sopra.
    #
    elif action == "CO_DR_RE":
        common.delete_driver(chat_id)
        bot.send_message(chat_id=chat_id,
                         text="Sei stato rimosso con successo dall'elenco degli autisti.")
    #
    # CO_US_RE = CONFIRM_USER_REMOVAL
    # Metodo di conferma rimozione utente, vedi sopra.
    #
    elif action == "CO_US_RE":
        user_debits = secret_data.users[chat_id]["Debit"]
        for creditor in user_debits:
            bot.send_message(chat_id=creditor,
                             text="ATTENZIONE! " + secret_data.users[chat_id]["Name"]
                                  + " si è cancellato da UberNEST. Ha ancora "
                                  + str(user_debits[creditor]) + " EUR di debito con te.")

        del secret_data.users[chat_id]
        if chat_id in secret_data.drivers:
            common.delete_driver(chat_id)
        bot.send_message(chat_id=chat_id, text="Sei stato rimosso con successo dal sistema.")
