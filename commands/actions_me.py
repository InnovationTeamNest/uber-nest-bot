# -*- coding: utf-8 -*-

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from data.data_api import is_registered, is_driver, get_all_debits, get_name, add_driver, delete_user, delete_driver
from routing.filters import create_callback_data as ccd, separate_callback_data
from util.keyboards import me_keyboard, trips_keyboard


def me(bot, update):
    if update.callback_query:
        me_cq(bot, update)
    else:
        me_cmd(bot, update)


# I due comandi seguenti sono equivalenti, uno viene chiamato se l'utente utilizza il comando /me,
# l'altro se torna al menù da una callback query

def me_cmd(bot, update):
    chat_id = str(update.message.chat_id)

    if is_registered(chat_id):
        bot.send_message(chat_id=chat_id, text="Cosa vuoi fare?", reply_markup=me_keyboard(chat_id))


def me_cq(bot, update):
    chat_id = str(update.callback_query.message.chat_id)

    if is_registered(chat_id):
        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Cosa vuoi fare?", reply_markup=me_keyboard(chat_id))


#
# Tutte le richieste inviate a questo metodo provengono dalla me_keyboard in keyboards.py.
# Da questo menù viene gestito per intero /me (al livello base), le rimozioni e aggiunte di autista,
# e le rimozioni degli utenti.
#
def me_handler(bot, update):
    action = separate_callback_data(update.callback_query.data)[1]
    chat_id = str(update.callback_query.message.chat_id)

    #
    # Da questo menù viene invocata la keyboard in keyboards.py.
    #
    if action == "TRIPS":
        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Viaggi (clicca su un viaggio per modificarlo):",
                              reply_markup=trips_keyboard(chat_id))
    #
    # Da questo menù è possibile iscriversi e disiscriversi dalla modalità autista.
    #
    elif action == "DRIVER":
        if is_driver(chat_id):
            keyboard = [
                [InlineKeyboardButton("✔ Sì", callback_data=ccd("ME", "CO_DR_RE")),
                 InlineKeyboardButton("❌ No", callback_data=ccd("ME_MENU"))]]
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text="Sei sicuro di voler confermare la tua rimozione dalla"
                                       " lista degli autisti? Se cambiassi idea, puoi sempre iscriverti"
                                       " di nuovo da /me. La cancellazione dal sistema comporterà il reset"
                                       " completo di tutti i viaggi, impostazioni e crediti.",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            keyboard = [
                [InlineKeyboardButton("✔ Sì", callback_data=ccd("ME", "ED_DR_SL")),
                 InlineKeyboardButton("❌ No", callback_data=ccd("ME_MENU"))]]
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
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
            [InlineKeyboardButton("✔ Sì", callback_data=ccd("ME", "CO_US_RE")),
             InlineKeyboardButton("❌ No", callback_data=ccd("ME_MENU"))]
        ]

        user_debits = get_all_debits(chat_id)
        debitors = []

        for creditor in user_debits:
            creditor_name = get_name(creditor)
            debitors.append(f" {creditor_name} - {str(user_debits[creditor])} EUR\n")

        message_text = [f"Sei sicuro di voler confermare la tua rimozione completa dal sistema?"
                        f" L'operazione è reversibile, ma tutte le tue prenotazioni e viaggi"
                        f" verranno cancellati per sempre."]

        if debitors:
            message_text.append(f"\n\nATTENZIONE! Hai debiti con le seguenti persone,"
                                f" in caso di cancellazione dal sistema"
                                f" verranno avvisate dei tuoi debiti non saldati!\n\n{''.join(debitors)}")

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id, text="".join(message_text),
                              reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # ED_DR_SL = EDIT_DRIVER_SLOTS
    # Questo menù permette di modificare gli slot a disposizione del guidatore.
    #
    elif action == "ED_DR_SL":
        # Inserisco 5 bottoni per i posti con la list comprehension
        keyboard = [
            [InlineKeyboardButton(str(i), callback_data=ccd("ME", "CO_DR", str(i))) for i in range(1, 6, 1)],
            [InlineKeyboardButton("↩ Indietro", callback_data=ccd("ME_MENU"))],
            [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
        ]
        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Inserisci il numero di posti disponibili nella tua macchina, autista escluso.",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # CO_DR = CONFIRM_DRIVER
    # Questo metodo svolge due diverse funzioni: se l'utente è un autista, è l'endpoint per la conferma
    # degli slot, altrimenti dell'iscrizione
    #
    elif action == "CO_DR":
        keyboard = [
            [InlineKeyboardButton("↩ Indietro", callback_data=ccd("ME_MENU"))],
            [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
        ]

        slots = int(separate_callback_data(update.callback_query.data)[2])
        if is_driver(chat_id):
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text="Numero di posti della vettura aggiornato con successo.",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            add_driver(chat_id, slots)
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text="Sei stato inserito nella lista degli autisti! Usa il menu /me per aggiungere"
                                       " viaggi, modificare i posti auto, aggiungere un messaggio da mostrare ai tuoi"
                                       " passeggeri ed altro.",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # CO_DR_RE = CONFIRM_DRIVER_REMOVAL
    # Metodo di conferma della rimozione di un autista, vedi sopra.
    #
    elif action == "CO_DR_RE":
        keyboard = [
            [InlineKeyboardButton("↩ Indietro", callback_data=ccd("ME_MENU"))],
            [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
        ]

        delete_driver(chat_id)
        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Sei stato rimosso con successo dall'elenco degli autisti.",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # CO_US_RE = CONFIRM_USER_REMOVAL
    # Metodo di conferma rimozione utente, vedi sopra.
    #
    elif action == "CO_US_RE":
        keyboard = [
            [InlineKeyboardButton("↩ Indietro", callback_data=ccd("ME_MENU"))],
            [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
        ]

        user_debits = get_all_debits(chat_id)
        for creditor in user_debits:
            bot.send_message(chat_id=creditor,
                             text=f"ATTENZIONE! [{get_name(chat_id)}](tg://user?id={chat_id})"
                             f" si è cancellato da UberNEST. Ha ancora "
                             f"{str(user_debits[creditor])} EUR di debito con te.",
                             parse_mode="Markdown")

        delete_user(chat_id)

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Sei stato rimosso con successo dal sistema.",
                              reply_markup=InlineKeyboardMarkup(keyboard))
