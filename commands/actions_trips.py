# -*- coding: utf-8 -*-
import math

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secret_data
from util import common
from util.filters import separate_callback_data, create_callback_data as ccd


def trips_handler(bot, update):
    """Metodo gestore delle chiamate indirizzate da "TRIPS", sottomenu di /me"""
    data = separate_callback_data(update.callback_query.data)
    action = data[1]
    chat_id = str(update.callback_query.from_user.id)

    if action == "NEW_TRIP":  # Chiamata sul bottone "Nuovo viaggio"
        keyboard = [
            [InlineKeyboardButton("per Povo", callback_data=ccd("NEWTRIP", "DAY", "Salita")),
             InlineKeyboardButton("per il NEST", callback_data=ccd("NEWTRIP", "DAY", "Discesa"))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]
        bot.send_message(chat_id=chat_id,
                         text="Vuoi aggiungere un viaggio verso il NEST o Povo? Ricorda che puoi aggiungere"
                              " un solo viaggio al giorno per direzione. Eventuali viaggi già presenti"
                              " verranno sovrascritti, passeggeri compresi.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # EDIT_TRIP viene chiamato in seguito alla pressione di un bottone di un dato viaggio.
    # Al suo interno è possibile modificare i passeggeri, l'orario, sospendere il viaggio
    # o cancellarlo.
    #
    elif action == "EDIT_TRIP":  # Chiamata sul bottone di un certo viaggio già presente
        direction, day = data[2:4]
        trip = secret_data.groups[direction][day][chat_id]

        if trip["Suspended"]:
            suspend_string = "Annullare la sospensione"
            text_string = " - SOSPESO"
            keyboard = []
        else:
            suspend_string = "Sospendere il viaggio"
            text_string = ""
            keyboard = [
                [InlineKeyboardButton("Modificare l'ora",
                                      callback_data=ccd("TRIPS", "EDIT_TRIP_HOUR", direction, day))],
                [InlineKeyboardButton("Modificare i passeggeri",
                                      callback_data=ccd("TRIPS", "EDIT_PASS", direction, day))]
            ]

        keyboard = keyboard + [
            [InlineKeyboardButton(suspend_string, callback_data=ccd("TRIPS", "SUS_TRIP", direction, day))],
            [InlineKeyboardButton("Cancellare il viaggio", callback_data=ccd("TRIPS", "REMOVE_TRIP", direction, day))],
            [InlineKeyboardButton("Tornare indietro", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Uscire", callback_data=ccd("EXIT"))]
        ]
        bot.send_message(chat_id=chat_id,
                         text="Viaggio selezionato:" + text_string + "\n"
                              + "\n🗓: " + day
                              + "\n➡: " + common.direction_to_name(direction)
                              + "\n🕓: " + trip["Time"]
                              + "\n👥 temporanei: "
                              + ",".join(secret_data.users[user]["Name"] for user in trip["Temporary"])
                              + "\n👥 permanenti: "
                              + ",".join(secret_data.users[user]["Name"] for user in trip["Permanent"])
                              + "\n👥 sospesi: "
                              + ",".join(secret_data.users[user]["Name"] for user in trip["SuspendedUsers"])
                              + "\n\nCosa vuoi fare?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # SUS_TRIP = SUSPEND_TRIP. Questa parte sospende temporaneamente (per una settimana) un viaggio,
    # rendendolo invisibile all'utente finale e bloccando presenti e future prenotazioni. La sospensione
    # viene sbloccata alle 02:00 del giorno successivo al viaggio bloccato, assieme alla gestione in night.py.
    # Il codice riconosce se il viaggio è già sospeso o meno e modifica il layout e le azioni di
    # conseguenza.
    #
    elif action == "SUS_TRIP":  # Sospensione del viaggio
        direction, day = data[2:4]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("TRIPS", "CO_SUS_TRIP", direction, day)),
             InlineKeyboardButton("No", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))]
        ]

        if secret_data.groups[direction][day][chat_id]["Suspended"]:
            message = "Vuoi annullare la sospensione di questo viaggio?"
        else:
            message = "La sospensione di un viaggio è valida per una sola volta e " \
                      + "comporta la sospensione di accreditamenti e prenotazioni " \
                      + "fino al giorno successivo al viaggio. Sei sicuro di voler " \
                      + "sospendere questo viaggio?"

        bot.send_message(chat_id=chat_id, text=message, reply_markup=InlineKeyboardMarkup(keyboard))
    # CO_SUS_TRIP = CONFERM_SUSPEND_TRIP
    # Metodo di conferma della sospensione appena avvenuta.
    elif action == "CO_SUS_TRIP":
        direction, day = data[2:4]

        if secret_data.groups[direction][day][chat_id]["Suspended"]:
            secret_data.groups[direction][day][chat_id]["Suspended"] = False
            message = "Il viaggio è ora operativo."
        else:
            secret_data.groups[direction][day][chat_id]["Suspended"] = True
            message = "Viaggio sospeso con successo."

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text=message,
                         reply_markup=InlineKeyboardMarkup(keyboard))
        common.alert_suspension(bot, direction, day, chat_id)
    #
    # Questi tre pezzi di codice vengono chiamate quando l'utente clicca su "Modifica l'ora" (in EDIT_TRIP).
    # Vengono eseguiti necessariamente in sequenza. Attenzione a fare modifiche per evitare di sforare il
    # limite di 64 byte dell'API per le callback.
    #
    # EDIT_TRIP_HOUR
    # Viene chiamato al momento dell'inserimento dell'ora durante la modifica dell'orario di un viaggio.
    elif action == "EDIT_TRIP_HOUR":
        direction, day = data[2:4]

        keyboard = [
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("TRIPS", "EDIT_TRIP_MIN", direction, day, i))
             for i in range(7, 14, 1)],
            [InlineKeyboardButton(str(i), callback_data=ccd("TRIPS", "EDIT_TRIP_MIN", direction, day, i))
             for i in range(14, 21, 1)],
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Scegli l'ora di partenza del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # EDIT_TRIP_MINUTES
    # Viene chiamato al momento dell'inserimento dei minuti durante la modifica dell'orario di un viaggio.
    elif action == "EDIT_TRIP_MIN":
        direction, day, hour = data[2:5]

        keyboard = [
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("TRIPS", "CO_EDIT_TRIP", direction, day, hour, i))
             for i in range(0, 30, 5)],
            [InlineKeyboardButton(str(i), callback_data=ccd("TRIPS", "CO_EDIT_TRIP", direction, day, hour, i))
             for i in range(30, 60, 5)],
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Scegli i minuti di partenza del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # CO_EDIT_TRIP = CONFIRM_EDIT_TRIP
    # Metodo chiamato per la conferma dell'orario appena modificato.
    elif action == "CO_EDIT_TRIP":
        direction, day, hour, minute = data[2:6]
        time = hour.zfill(2) + ":" + minute.zfill(2)

        trip = secret_data.groups[direction][str(day)][str(chat_id)]

        trip["Time"] = str(time)

        for user_group in trip["Permanent"], trip["Temporary"]:
            for user in user_group:
                bot.send_message(chat_id=user,
                                 text=secret_data.users[chat_id]["Name"] + " ha spostato l'orario del viaggio di "
                                      + day + common.direction_to_name(direction) + " alle " + str(time) + ".")

        bot.send_message(chat_id=chat_id, text="Nuovo orario di partenza:\n"
                                               + day + " alle "
                                               + str(time) + " " + common.direction_to_name(direction))
    #
    # I seguenti comandi sono utilizzati per modificare la lista dei viaggitori di un
    # dato viaggio e rimuoverlo. Il metodo per aggiungere nuovi passeggeri si trova
    # in fondo al documento.
    #
    # EDIT_PASS - Comando chiamato una volta premuto il bottone della persona da prenotare
    elif action == "EDIT_PASS":
        direction, day = data[2:4]

        trip = secret_data.groups[direction][day][chat_id]

        permanent_users = trip["Permanent"]
        temporary_users = trip["Temporary"]
        suspended_users = trip["SuspendedUsers"]

        # Lista delle persone prenotate divise per Permanente e Temporanea

        user_lines = [[InlineKeyboardButton(secret_data.users[user]["Name"] + " - Permanente",
                                            callback_data=ccd("TRIPS", "REMOVE_PASS", direction, day, user,
                                                              "Permanent"))]
                      for user in permanent_users] \
                     + [[InlineKeyboardButton(secret_data.users[user]["Name"] + " - Temporaneo",
                                              callback_data=ccd("TRIPS", "REMOVE_PASS", direction, day, user,
                                                                "Temporary"))]
                        for user in temporary_users] \
                     + [[InlineKeyboardButton(secret_data.users[user]["Name"] + " - Permanente (SOSPESO)",
                                              callback_data=ccd("TRIPS", "REMOVE_PASS", direction, day, user,
                                                                "SuspendedUsers"))]
                        for user in suspended_users]

        keyboard = user_lines + [
            [InlineKeyboardButton("Nuovo passeggero", callback_data=ccd("ADD_PASS", "SELECT", direction, day, "0"))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Clicca su un passeggero per rimuoverlo"
                                               + " dal tuo viaggio, oppure aggiungine uno"
                                               + " manualmente.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # REMOVE_PASS - Comando chiamato in seguito a pressione del bottone contenente un utente di un viaggio
    elif action == "REMOVE_PASS":
        direction, day, user, mode = data[2:6]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("TRIPS", "CO_RE_PA", direction, day, user, mode)),
             InlineKeyboardButton("No", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler rimuovere questo passeggero?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # CO_RE_PA = CONFIRM_REMOVE_PASSENGER
    # Comando chiamato in caso di rispsota positiva al precedente comando
    elif action == "CO_RE_PA":
        direction, day, user, mode = data[2:6]
        secret_data.groups[direction][day][chat_id][mode].remove(user)
        bot.send_message(chat_id=chat_id, text="Passeggero rimosso con successo.")
        bot.send_message(chat_id=user,
                         text=secret_data.users[chat_id]["Name"] + " ti ha rimosso dal viaggio di "
                              + day + " alle " + secret_data.groups[direction][day][chat_id]["Time"]
                              + " " + common.direction_to_name(direction) + ".")
    # Comando chiamato quando si clicca su "Rimuovi viaggio" nella vista viaggio
    elif action == "REMOVE_TRIP":
        direction, day = data[2:4]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("TRIPS", "CO_RE_TR", direction, day)),
             InlineKeyboardButton("No", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Sei sicuro di voler cancellare questo viaggio?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # CO_RE_TR = CONFIRM_REMOVE_TRIP
    # Comando chiamato in caso di risposta positiva al precedente comando
    elif action == "CO_RE_TR":
        direction, day = data[2:4]
        del secret_data.groups[direction][day][chat_id]

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Viaggio cancellato con successo.",
                         reply_markup=InlineKeyboardMarkup(keyboard))


def add_passenger(bot, update):
    """
    Metodo chiamato in seguito alla pressione di un bottone contenente un nome di un passeggero
    da aggiungere. Questo metodo può essere chiamato solo dal sottomenù trips.

    I potenziali passeggeri vengono listati su più pagine per evitare messaggi infiniti. A ogni pagina è
    associata un bottone che permette di aprirla immediatamente. In ogni pagina vi sono PAGE_SIZE persone,
    costante definita in util/common.py
    """
    chat_id = str(update.callback_query.from_user.id)
    data = separate_callback_data(update.callback_query.data)
    action = data[1]

    # Comando chiamato dalla vista viaggio per aggiungere un passeggero
    if action == "SELECT":
        direction, day, page = data[2:5]

        keyboard = []
        page = int(page)
        users = sorted(  # Resituisce una lista di tuple del tipo (Nome, ID)
            [(secret_data.users[user]["Name"], user)
             for user in secret_data.users if user != chat_id]
        )

        for index in range(common.PAGE_SIZE * page, common.PAGE_SIZE * (page + 1), 1):
            try:
                name, id = users[index]
                keyboard.append([InlineKeyboardButton(
                    name, callback_data=ccd("ADD_PASS", "MODE", direction, day, id))])
            except IndexError:
                break

        # Aggiungo un bottone per ogni pagina, in quanto la lista è troppo grande
        page_buttons = []
        for index in range(0, int(math.ceil(len(users) / common.PAGE_SIZE)), 1):
            if index == page:
                text = "☑"
            else:
                text = str(index + 1)

            page_buttons.append(InlineKeyboardButton(
                text, callback_data=ccd("ADD_PASS", "SELECT", direction, day, index))
            )

        keyboard.append(page_buttons)
        keyboard.append([InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_PASS", direction, day))])
        keyboard.append([InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))])

        bot.send_message(chat_id=chat_id, text="Seleziona un passeggero da aggiungere al tuo viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # Comando chiamato una volta premuto il bottone della persona da prenotare
    elif action == "MODE":
        direction, day, user = data[2:5]

        keyboard = [
            [InlineKeyboardButton("Temporanea", callback_data=ccd("ADD_PASS", "CONFIRM",
                                                                  direction, day, user, "Temporary"))],
            [InlineKeyboardButton("Permanente", callback_data=ccd("ADD_PASS", "CONFIRM",
                                                                  direction, day, user, "Permanent"))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("ADD_PASS", "SELECT", direction, day, "0"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Scegli la modalità di prenotazione.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    # Comando chiamato una volta premuto il bottone della persona da prenotare e scelta la modalità
    elif action == "CONFIRM":
        direction, day, user, mode = data[2:6]

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        trip = secret_data.groups[direction][day][chat_id]
        occupied_slots = len(trip["Permanent"]) + len(trip["Temporary"])
        total_slots = secret_data.drivers[chat_id]["Slots"]

        if occupied_slots >= total_slots:
            bot.send_message(chat_id=chat_id, text="Temo che il tuo amico dovrà andare a piedi, i posti sono finiti.",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        elif str(user) in trip["Temporary"] or str(user) in trip["Permanent"]:
            bot.send_message(chat_id=chat_id, text="Questa persona si è già prenotata in questo viaggio!",
                             reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            trip[mode].append(str(user))

            driver_text = "Prenotazione completata. Dati del viaggio:" \
                          + "\n\n👤: " + str(secret_data.users[user]["Name"]) \
                          + "\n🗓: " + day \
                          + "\n🕓: " + trip["Time"] \
                          + "\n➡: " + common.direction_to_name(direction) \
                          + "\n🔁: " + common.localize_mode(mode)

            user_text = str(secret_data.users[chat_id]["Name"]) \
                        + " ha effettuato una nuova prenotazione a tuo nome nel suo viaggio: " \
                        + "\n🗓: " + day \
                        + "\n🕓: " + trip["Time"] \
                        + "\n➡: " + common.direction_to_name(direction) \
                        + "\n🔁: " + common.localize_mode(mode)

            if "Location" in trip:
                driver_text += "\n📍: " + trip["Location"]
                user_text += "\n📍: " + trip["Location"]

            bot.send_message(chat_id=chat_id, text=driver_text, reply_markup=InlineKeyboardMarkup(keyboard))
            bot.send_message(chat_id=user, text=user_text)


#
# Questo metodo viene chiamato da trips_handler().
# Da questo metodo è possibile inserire per intero un nuovo viaggio di un autista.
#
def newtrip_handler(bot, update):
    data = separate_callback_data(update.callback_query.data)
    chat_id = str(update.callback_query.from_user.id)
    mode = data[1]

    #
    # Metodo per l'inserimento del giorno
    # Dati in entrata: "NEWTRIP", "DAY", direction
    #
    if mode == "DAY":
        data = data[2:]
        keyboard = []

        for day in common.work_days:
            keyboard.append(InlineKeyboardButton(day[:2], callback_data=ccd("NEWTRIP", "HOUR", day, *data)))

        keyboard = [keyboard,
                    [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS"))],
                    [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]]

        bot.send_message(chat_id=chat_id, text="Scegli il giorno della settimana del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # Metodo per l'inserimento dell'ora
    # Dati in entrata: "NEWTRIP", "HOUR", day, direction
    #
    elif mode == "HOUR":
        data = data[2:]
        keyboard = [
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("NEWTRIP", "MINUTE", str(i), *data))
             for i in range(7, 14, 1)],
            [InlineKeyboardButton(str(i), callback_data=ccd("NEWTRIP", "MINUTE", str(i), *data))
             for i in range(14, 21, 1)],
            [InlineKeyboardButton("Indietro", callback_data=ccd("NEWTRIP", "MINUTE", *data[1:]))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id, text="Scegli l'ora di partenza del viaggio. ",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # Metodo per l'inserimento dei minuti
    # Dati in entrata: "NEWTRIP", "HOUR", hour, day, direction
    #
    elif mode == "MINUTE":
        data = data[2:]
        keyboard = [
            [InlineKeyboardButton(str(i).zfill(2), callback_data=ccd("NEWTRIP", "CONFIRM", str(i), *data))
             for i in range(0, 30, 5)],
            [InlineKeyboardButton(str(i), callback_data=ccd("NEWTRIP", "CONFIRM", str(i), *data))
             for i in range(30, 60, 5)],
            [InlineKeyboardButton("Indietro", callback_data=ccd("NEWTRIP", "CONFIRM", *data[1:]))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.send_message(chat_id=chat_id,
                         text="Scegli i minuti di partenza del viaggio.",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # Metodo di conferma finale
    # Dati in entrata: "NEWTRIP", "CONFIRM", minute, hour, day, direction
    #
    elif mode == "CONFIRM":
        minute, hour, day, direction = data[2:]
        time = hour.zfill(2) + ":" + minute.zfill(2)

        secret_data.groups[direction][str(day)][str(chat_id)] = {"Time": str(time),
                                                                 "Permanent": [],
                                                                 "Temporary": [],
                                                                 "SuspendedUsers": [],
                                                                 "Suspended": False}

        user_text = "Viaggio aggiunto con successo:" \
                    + "\n\n➡: " + common.direction_to_name(direction) \
                    + "\n🗓: " + day \
                    + "\n🕓: " + str(time)

        bot.send_message(chat_id=chat_id, text=user_text)
    else:
        bot.send_message(chat_id=chat_id, text="Spiacente, si è verificato un errore. Riprova più tardi.")
