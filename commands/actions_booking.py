# -*- coding: utf-8 -*-
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import secret_data
import util.common as common
from util.filters import create_callback_data as ccd, separate_callback_data
from util.keyboards import booking_keyboard


def prenota(bot, update):
    """
    Comando base chiamato dall'utente. Ha tre modalità:
    - Prenotazione temporanea
    - Prenotazione permanente
    - Vista prenotazioni
    """
    if update.callback_query:
        chat_id = update.callback_query.from_user.id
        try:
            update.callback_query.message.delete()
        except BadRequest:
            print("Failed to delete previous message", file=sys.stderr)
    else:
        chat_id = update.message.chat_id

    if str(chat_id) in secret_data.users:
        keyboard = [[InlineKeyboardButton("Prenotare una-tantum",
                                          callback_data=ccd("BOOKING", "NEW", "Temporary"))],
                    [InlineKeyboardButton("Prenotare in maniera permanente",
                                          callback_data=ccd("BOOKING", "NEW", "Permanent"))],
                    [InlineKeyboardButton("Gestire le mie prenotazioni",
                                          callback_data=ccd("EDIT_BOOK", "LIST"))],
                    [InlineKeyboardButton("Uscire", callback_data=ccd("EXIT"))]]
        bot.send_message(chat_id=chat_id,
                         text="Cosa vuoi fare?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        bot.send_message(chat_id=chat_id,
                         text="Per effettuare una prenotazione, registrati con /registra.")


def booking_handler(bot, update):
    """
    Gestore dei metodi delle prenotazioni. Da questo menù è possibile aggiungere prenotazioni.
    """
    data = separate_callback_data(update.callback_query.data)
    action = data[1]
    chat_id = str(update.callback_query.from_user.id)

    #
    # Dati in entrata ("BOOKING", "NEW", mode)
    # Questo metodo viene automaticamente chiamato con la modalità preselezionata. I viaggi mostrati sono
    # comunque uguali e differiscono solo per la callback_query a loro assegnata. Il messaggio di avviso invece
    # cambia a seconda della modalità scelta. Infine, il menù è limitato a un uso entro un range orario definito
    # in common.py per evitare prenotazioni notturne assurde.
    #
    if action == "NEW":
        if common.booking_time():
            mode = data[2]

            if mode == "Temporary":
                text = "Si ricorda che le prenotazioni una-tantum vengono automaticamente cancellate ed" \
                       + " addebitate il giorno dopo la prenotazione. E' possibile prenotarsi a un viaggio" \
                       + " già avvenuto, ma verrà addebitato comunque."
            elif mode == "Permanent":
                text = "Si ricorda che le prenotazioni permanenti verranno addebitate anche per i viaggi" \
                       + " prenotati per la giornata corrente."
            else:
                text = ""

            user_keyboard = [
                [InlineKeyboardButton(day[:2],  # Abbreviazione del giorno
                                      callback_data=ccd("BOOKING", "DAY", mode, day)) for day in common.work_days],
                [InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING_MENU"))],
                [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
            ]

            bot.send_message(chat_id=chat_id, text=text + "\n\nScegli la data della prenotazione.",
                             reply_markup=InlineKeyboardMarkup(user_keyboard))
        else:
            bot.send_message(chat_id=chat_id,
                             text="Mi dispiace, è possibile effettuare prenotazioni"
                                  + " tramite UberNEST solo dalle "
                                  + common.booking_start.strftime("%H:%M") + " alle "
                                  + common.booking_end.strftime("%H:%M") + ".")
    #
    # Dati in entrata ("BOOKING", "DAY", mode, day)
    # Questo menù viene chiamato rispettivamente dal metodo sopra (BOOKING/NEW) e dai visualizzatori
    # delle prenotazioni dei singoli giorni (/lunedi, /martedi, etc...).
    elif action == "DAY":
        mode, day = data[2:4]
        bot.send_message(chat_id=chat_id, text="Viaggi disponibili per " + day.lower() + ":",
                         reply_markup=booking_keyboard(mode, day))
    #
    # Dati in entrata ("BOOKING", "CONFIRM", direction, day, driver, mode)
    # Messaggio finale di conferma all'utente e all'autista. Il metodo calcola se la prenotazione scelta è
    # legale (ovvero che è disponibile spazio nell'auto, che il passeggero non è l'autista e che non si è
    # già prenotato). In caso positivo viene avvisato anche l'autista dell'avvenuta prenotazione
    #
    elif action == "CONFIRM":
        direction, day, driver, mode = data[2:]

        user_keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING", "DAY", mode, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        driver_keyboard = [
            [InlineKeyboardButton("Conferma", callback_data=ccd("ALERT_USER", "CO_BO", direction, day, chat_id, mode))]
        ]

        trip = secret_data.groups[direction][day][driver]
        occupied_slots = len(trip["Permanent"]) + len(trip["Temporary"])
        total_slots = secret_data.drivers[driver]["Slots"]

        if chat_id == driver:
            bot.send_message(chat_id=chat_id, text="Sei tu l'autista!",
                             reply_markup=InlineKeyboardMarkup(user_keyboard))
        elif occupied_slots >= total_slots:
            bot.send_message(chat_id=chat_id, text="Macchina piena, vai a piedi LOL",
                             reply_markup=InlineKeyboardMarkup(user_keyboard))
        elif chat_id in trip["Temporary"] or chat_id in trip["Permanent"] or chat_id in trip["SuspendedUsers"]:
            bot.send_message(chat_id=chat_id, text="Ti sei già prenotato in questa data con questa persona!",
                             reply_markup=InlineKeyboardMarkup(user_keyboard))
        else:
            # Si attende conferma dall'autista prima di aggiungere
            user_text = "Prenotazione completata. Dati del viaggio:" \
                        + "\n\n🚗: " + str(secret_data.users[driver]["Name"]) \
                        + "\n🗓: " + day \
                        + "\n🕓: " + trip["Time"] \
                        + "\n➡: " + common.direction_to_name(direction) \
                        + "\n🔁: " + common.localize_mode(mode) \
                        + "\n\nRiceverai una conferma dall'autista il prima possibile."

            driver_text = "Hai una nuova prenotazione: " \
                          + "\n\n👤: " + str(secret_data.users[chat_id]["Name"]) \
                          + " (" + str(total_slots - occupied_slots - 1) + " posti rimanenti)" \
                          + "\n🗓: " + day \
                          + "\n🕓: " + trip["Time"] \
                          + "\n➡: " + common.direction_to_name(direction) \
                          + "\n🔁: " + common.localize_mode(mode) \
                          + ".\n\nPer favore, conferma la presa visione della prenotazione. In caso negativo," \
                          + " la prenotazione verrà considerata non valida."

            # Eventuale aggiunta del luogo di ritrovo
            if "Location" in trip:
                user_text += "\n📍: " + trip["Location"]
                driver_text += "\n📍: " + trip["Location"]

            bot.send_message(chat_id=chat_id, text=user_text, reply_markup=InlineKeyboardMarkup(user_keyboard))
            bot.send_message(chat_id=driver, text=driver_text, reply_markup=InlineKeyboardMarkup(driver_keyboard))


def edit_booking(bot, update):
    """
    Questo metodo viene chiamato al momento della richiesta di visione della lista delle prenotazioni da 
    parte dell'utente. Le prenotazione vengono prese tramite query dal metodo search_by_booking presente
    in common.py. Dal menù, una volta selezionata una prenotazione, è possibile cancellarla oppure sospenderla
    a lato utente, ovvero bloccarla per una settimana.
    """
    chat_id = str(update.callback_query.from_user.id)
    data = separate_callback_data(update.callback_query.data)
    action = data[1]

    #
    #  Comando base chiamato dal metodo prenota. Effettua una query di tutti i viaggi presentandoli
    #  sottoforma di bottoni all'utente.
    #
    if action == "LIST":
        bookings = common.search_by_booking(chat_id)

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("BOOKING_MENU"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        if len(bookings) > 0:
            user_keyboard = []

            for item in bookings:
                direction, day, driver, mode, time = item

                if secret_data.groups[direction][day][driver]["Suspended"]:
                    tag = " - SOSPESA"
                else:
                    tag = " - 🕓 " + day + " alle " + str(time)

                # Aggiunta del bottone
                user_keyboard.append([InlineKeyboardButton(
                    "🚗 " + secret_data.users[driver]["Name"] + tag
                    + "\n➡ " + common.direction_to_name(direction) + " - " + common.localize_mode(mode),
                    callback_data=ccd("EDIT_BOOK", "ACTION", direction, day, driver, mode))])

            bot.send_message(chat_id=chat_id,
                             text="Clicca su una prenotazione per cancellarla o sospenderla.",
                             reply_markup=InlineKeyboardMarkup(user_keyboard + keyboard))
        else:
            bot.send_message(chat_id=chat_id, text="Mi dispiace, ma non hai prenotazioni all'attivo.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # Menù disponibile all'utente una volta selezionato un viaggio. I bottoni cambiano a seconda della prenotazione:
    # Temporanea -> solo cancellazione
    # Permanente e sospesa -> sospensione e cancellazione
    #
    elif action == "ACTION":
        direction, day, driver, mode = data[2:]
        keyboard = [
            [InlineKeyboardButton("Annulla prenotazione", callback_data=ccd("EDIT_BOOK", "DELETION",
                                                                            direction, day, driver, mode))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("EDIT_BOOK", "LIST"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        text_string = ""

        if mode == "Permanent":
            keyboard.insert(0, [InlineKeyboardButton(
                "Sospendi prenotazione", callback_data=ccd("EDIT_BOOK", "SUS_BOOK", direction, day, driver, mode))])

        elif mode == "SuspendedUsers":
            keyboard.insert(0, [InlineKeyboardButton(
                "Annulla sospensione prenotazione",
                callback_data=ccd("EDIT_BOOK", "SUS_BOOK", direction, day, driver, mode))])
            text_string += " - SOSPESA dall'utente"

        if secret_data.groups[direction][day][driver]["Suspended"]:
            text_string += " - SOSPESA dall'autista"

        bot.send_message(chat_id=chat_id,
                         text="Prenotazione selezionata:" + text_string + "\n"
                              + "\n🚗:" + secret_data.users[driver]["Name"]
                              + "\n🗓: " + day
                              + "\n➡: " + common.direction_to_name(direction)
                              + "\n🕓: " + secret_data.groups[direction][day][driver]["Time"]
                              + "\n🔁: " + common.localize_mode(mode),
                         reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # SUS_BOOK = SUSPEND_BOOKING
    #
    elif action == "SUS_BOOK":
        booking = data[2:]
        mode = booking[3]

        keyboard = [
            InlineKeyboardButton("Sì", callback_data=ccd("EDIT_BOOK", "CO_SUS_BOOK", *booking)),
            InlineKeyboardButton("No", callback_data=ccd("EDIT_BOOK", "LIST"))
        ]

        if mode == "Permanent":
            message = "Si ricorda che la sospensione di una prenotazione è valida per" \
                      " una sola settimana.\n\nSei sicuro di voler sospendere questo viaggio?"

        elif mode == "SuspendedUsers":
            message = "Vuoi rendere di nuovo operativa questa prenotazione?"

        else:
            message = ""

        bot.send_message(chat_id=chat_id, text=message,
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    #
    # CO_SUS_BOOK = CONFIRM_SUSPEND_BOOKING
    # Il metodo scambia la chiave di un utente da Permanente a SuspendUsers e vice-versa.
    #
    elif action == "CO_SUS_BOOK":
        direction, day, driver, mode = data[2:]
        trip = secret_data.groups[direction][day][driver]

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("EDIT_BOOK", "LIST"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        if mode == "Permanent":
            trip["Permanent"].remove(chat_id)
            trip["SuspendedUsers"].append(chat_id)

            user_message = "Prenotazione sospesa. Verrà ripristinata il prossimo viaggio."
            driver_message = secret_data.users[chat_id]["Name"] + " ha sospeso la sua prenotazione permanente" \
                             + " per " + day.lower() + " " + common.direction_to_name(direction) + "."

        elif mode == "SuspendedUsers":
            occupied_slots = len(trip["Permanent"]) + len(trip["Temporary"])
            total_slots = secret_data.drivers[driver]["Slots"]

            if occupied_slots >= total_slots:
                # Può capitare che mentre un passeggero ha reso la propria prenotazione sospesa,
                # altre persone hanno preso il suo posto.
                bot.send_message(chat_id=chat_id, text="Mi dispiace, ma non puoi rendere operativa la"
                                                       + " tua prenotazione in quanto la macchina è ora piena."
                                                       + "Contatta " + secret_data.users[driver]["Name"]
                                                       + " per risolvere la questione.",
                                 reply_markup=InlineKeyboardMarkup(keyboard))
                return

            trip["Permanent"].append(chat_id)
            trip["SuspendedUsers"].remove(chat_id)

            user_message = "La prenotazione è di nuovo operativa."
            driver_message = secret_data.users[chat_id]["Name"] + " ha reso operativa la sua prenotazione permanente" \
                             + " di " + day.lower() + " " + common.direction_to_name(direction) + "."

        else:
            user_message = driver_message = ""

        bot.send_message(chat_id=chat_id, text=user_message,
                         reply_markup=InlineKeyboardMarkup(keyboard))
        bot.send_message(chat_id=driver, text=driver_message)
    #
    # Metodo per cancellare per sempre una data prenotazione.
    #
    elif action == "DELETION":
        booking = data[2:]

        keyboard = [
            InlineKeyboardButton("Sì", callback_data=ccd("EDIT_BOOK", "CO_DEL", *booking)),
            InlineKeyboardButton("No", callback_data=ccd("EDIT_BOOK", "LIST"))
        ]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup([keyboard]))
    #
    # CO_DEL = CONFIRM_DELETION
    #
    elif action == "CO_DEL":
        direction, day, driver, mode = data[2:]
        secret_data.groups[direction][day][driver][mode].remove(chat_id)

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("EDIT_BOOK", "LIST"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Prenotazione cancellata con successo.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
        bot.send_message(chat_id=driver,
                         text=secret_data.users[chat_id]["Name"]
                              + " ha cancellato la prenotazione per " + day + " "
                              + common.direction_to_name(direction) + ".")


def alert_user(bot, update):
    chat_id = str(update.callback_query.from_user.id)
    data = separate_callback_data(update.callback_query.data)
    action = data[1]

    if action == "CO_BO":
        direction, day, user, mode = data[2:]  # Utente della prenotazione
        secret_data.groups[direction][day][chat_id][mode].append(user)
        bot.send_message(chat_id=user, text=secret_data.users[chat_id]["Name"] + " ha confermato la tua prenotazione.")
        bot.send_message(chat_id=chat_id, text="Prenotazione confermata con successo.")
