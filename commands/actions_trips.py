# -*- coding: utf-8 -*-
import math

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secrets
from util import common
from util.filters import separate_callback_data, create_callback_data as ccd


def trips_handler(bot, update):
    """Metodo gestore delle chiamate indirizzate da "TRIPS", sottomenu di /me"""
    data = separate_callback_data(update.callback_query.data)
    action = data[1]
    chat_id = str(update.callback_query.message.chat_id)

    if action == "NEW_TRIP":  # Chiamata sul bottone "Nuovo viaggio"
        keyboard = [
            [InlineKeyboardButton("per Povo", callback_data=ccd("NEWTRIP", "DAY", "Salita")),
             InlineKeyboardButton("per il NEST", callback_data=ccd("NEWTRIP", "DAY", "Discesa"))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
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
        trip = secrets.groups[direction][day][chat_id]

        if trip["Suspended"]:
            suspend_string = "Annullare la sospensione"
            text_string = " - 🚫 Sospeso"
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

        keyboard += [
            [InlineKeyboardButton(suspend_string, callback_data=ccd("TRIPS", "SUS_TRIP", direction, day))],
            [InlineKeyboardButton("Cancellare il viaggio", callback_data=ccd("TRIPS", "REMOVE_TRIP", direction, day))],
            [InlineKeyboardButton("Tornare indietro", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Uscire", callback_data=ccd("EXIT"))]
        ]
        temporary_passengers = ','.join(secrets.users[user]['Name'] for user in trip['Temporary'])
        permanent_passengers = ','.join(secrets.users[user]['Name'] for user in trip['Permanent'])
        suspended_passengers = ','.join(secrets.users[user]['Name'] for user in trip['SuspendedUsers'])

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=f"Viaggio selezionato: {text_string}"
                                   f"\n\n🗓 {day}"
                                   f"\n{common.dir_name(direction)}"
                                   f"\n🕓 {trip['Time']}"
                                   f"\n👥 temporanei: {temporary_passengers}"
                                   f"\n👥 permanenti: {permanent_passengers}"
                                   f"\n👥 sospesi: {suspended_passengers}"
                                   f"\n\nCosa vuoi fare?",
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

        if secrets.groups[direction][day][chat_id]["Suspended"]:
            message = "Vuoi annullare la sospensione di questo viaggio?"
        else:
            message = "La sospensione di un viaggio è valida per una sola volta e " \
                      "comporta la sospensione di accreditamenti e prenotazioni " \
                      "fino al giorno successivo al viaggio. Sei sicuro di voler " \
                      "sospendere questo viaggio?"

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=message, reply_markup=InlineKeyboardMarkup(keyboard))
    # CO_SUS_TRIP = CONFERM_SUSPEND_TRIP
    # Metodo di conferma della sospensione appena avvenuta.
    elif action == "CO_SUS_TRIP":
        direction, day = data[2:4]

        if secrets.groups[direction][day][chat_id]["Suspended"]:
            secrets.groups[direction][day][chat_id]["Suspended"] = False
            message = "Il viaggio è ora operativo."
        else:
            secrets.groups[direction][day][chat_id]["Suspended"] = True
            message = "Viaggio sospeso con successo."

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=message,
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

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Scegli l'ora di partenza del viaggio.",
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

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Scegli i minuti di partenza del viaggio.",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    # CO_EDIT_TRIP = CONFIRM_EDIT_TRIP
    # Metodo chiamato per la conferma dell'orario appena modificato.
    elif action == "CO_EDIT_TRIP":
        direction, day, hour, minute = data[2:6]
        time = f"{hour.zfill(2)}:{minute.zfill(2)}"

        trip = secrets.groups[direction][str(day)][str(chat_id)]
        trip["Time"] = str(time)

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        for user_group in trip["Permanent"], trip["Temporary"]:
            for user in user_group:
                bot.send_message(chat_id=user,
                                 text=f"{secrets.users[chat_id]['Name']} ha spostato l'orario del viaggio di "
                                      f"{day} {common.dir_name(direction)} alle {str(time)}.")

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=f"Nuovo orario di partenza:\n{day} alle "
                                   f"{str(time)} {common.dir_name(direction)}",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # I seguenti comandi sono utilizzati per modificare la lista dei viaggitori di un
    # dato viaggio e rimuoverlo. Il metodo per aggiungere nuovi passeggeri si trova
    # in fondo al documento.
    #
    # EDIT_PASS - Comando chiamato una volta premuto il bottone della persona da prenotare
    elif action == "EDIT_PASS":
        direction, day = data[2:4]

        trip = secrets.groups[direction][day][chat_id]

        permanent_users = trip["Permanent"]
        temporary_users = trip["Temporary"]
        suspended_users = trip["SuspendedUsers"]

        # Lista delle persone prenotate divise per Permanente e Temporanea

        user_lines = [[InlineKeyboardButton(f"{secrets.users[user]['Name']} - Permanente",
                                            callback_data=ccd("TRIPS", "REMOVE_PASS", direction, day, user,
                                                              "Permanent"))] for user in permanent_users] \
                     + [[InlineKeyboardButton(f"{secrets.users[user]['Name']} - Temporaneo",
                                              callback_data=ccd("TRIPS", "REMOVE_PASS", direction, day, user,
                                                                "Temporary"))]
                        for user in temporary_users] \
                     + [[InlineKeyboardButton(f"{secrets.users[user]['Name']} - Permanente (SOSPESO)",
                                              callback_data=ccd("TRIPS", "REMOVE_PASS", direction, day, user,
                                                                "SuspendedUsers"))]
                        for user in suspended_users]

        keyboard = user_lines + [
            [InlineKeyboardButton("Nuovo passeggero", callback_data=ccd("ADD_PASS", "SELECT", direction, day, "0"))],
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Clicca su un passeggero per rimuoverlo"
                                   " dal tuo viaggio, oppure aggiungine uno"
                                   " manualmente.",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    # REMOVE_PASS - Comando chiamato in seguito a pressione del bottone contenente un utente di un viaggio
    elif action == "REMOVE_PASS":
        direction, day, user, mode = data[2:6]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("TRIPS", "CO_RE_PA", direction, day, user, mode)),
             InlineKeyboardButton("No", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))]
        ]

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Sei sicuro di voler rimuovere questo passeggero?",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    # CO_RE_PA = CONFIRM_REMOVE_PASSENGER
    # Comando chiamato in caso di rispsota positiva al precedente comando
    elif action == "CO_RE_PA":
        direction, day, user, mode = data[2:6]
        secrets.groups[direction][day][chat_id][mode].remove(user)

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Passeggero rimosso con successo.",
                              reply_markup=InlineKeyboardMarkup(keyboard))

        bot.send_message(chat_id=user,
                         text=f"Sei stato rimosso dal seguente viaggio: "
                              f"\n\n🚗 {secrets.users[chat_id]['Name']}"
                              f"\n🗓 {day}"
                              f"\n🕓 {secrets.groups[direction][day][chat_id]['Time']}"
                              f"\n{common.dir_name(direction)}")
    # Comando chiamato quando si clicca su "Rimuovi viaggio" nella vista viaggio
    elif action == "REMOVE_TRIP":
        direction, day = data[2:4]

        keyboard = [
            [InlineKeyboardButton("Sì", callback_data=ccd("TRIPS", "CO_RE_TR", direction, day)),
             InlineKeyboardButton("No", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))]
        ]

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Sei sicuro di voler cancellare questo viaggio?",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    # CO_RE_TR = CONFIRM_REMOVE_TRIP
    # Comando chiamato in caso di risposta positiva al precedente comando
    elif action == "CO_RE_TR":
        direction, day = data[2:4]
        del secrets.groups[direction][day][chat_id]

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("ME", "TRIPS"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Viaggio cancellato con successo.",
                              reply_markup=InlineKeyboardMarkup(keyboard))


def add_passenger(bot, update):
    """
    Metodo chiamato in seguito alla pressione di un bottone contenente un nome di un passeggero
    da aggiungere. Questo metodo può essere chiamato solo dal sottomenù trips.

    I potenziali passeggeri vengono listati su più pagine per evitare messaggi infiniti. A ogni pagina è
    associata un bottone che permette di aprirla immediatamente. In ogni pagina vi sono PAGE_SIZE persone,
    costante definita in util/common.py
    """
    chat_id = str(update.callback_query.message.chat_id)
    data = separate_callback_data(update.callback_query.data)
    action = data[1]

    # Comando chiamato dalla vista viaggio per aggiungere un passeggero
    if action == "SELECT":
        direction, day, page = data[2:5]

        keyboard = []
        page = int(page)
        users = sorted(  # Resituisce una lista di tuple del tipo (Nome, ID)
            [(secrets.users[user]["Name"], user)
             for user in secrets.users if user != chat_id]
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

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Seleziona un passeggero da aggiungere al tuo viaggio.",
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

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Scegli la modalità di prenotazione.",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    # Comando chiamato una volta premuto il bottone della persona da prenotare e scelta la modalità
    elif action == "CONFIRM":
        direction, day, user, mode = data[2:6]

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS", "EDIT_TRIP", direction, day))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        trip = secrets.groups[direction][day][chat_id]
        occupied_slots = len(trip["Permanent"]) + len(trip["Temporary"])
        total_slots = secrets.drivers[chat_id]["Slots"]

        if user in trip["Temporary"] or user in trip["Permanent"]:
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text="Questa persona si è già prenotata in questo viaggio!",
                                  reply_markup=InlineKeyboardMarkup(keyboard))

        elif occupied_slots >= total_slots:
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text="Temo che il tuo amico dovrà andare a piedi, i posti sono finiti.",
                                  reply_markup=InlineKeyboardMarkup(keyboard))

        else:
            trip[mode].append(str(user))

            bot.send_message(chat_id=user,
                             text=f"{secrets.users[chat_id]['Name']}"
                                  f" ha effettuato una nuova prenotazione a tuo nome nel suo viaggio: "
                                  f"\n\n🗓 {day}"
                                  f"\n🕓 {trip['Time']}"
                                  f"\n{common.dir_name(direction)}"
                                  f"\n{common.mode_name(mode)}")

            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  reply_markup=InlineKeyboardMarkup(keyboard),
                                  text="Prenotazione completata. Dati del viaggio:"
                                       f"\n\n👤 {str(secrets.users[user]['Name'])}"
                                       f"\n🗓 {day}"
                                       f"\n🕓 {trip['Time']}"
                                       f"\n{common.dir_name(direction)}"
                                       f"\n{common.mode_name(mode)}")


#
# Questo metodo viene chiamato da trips_handler().
# Da questo metodo è possibile inserire per intero un nuovo viaggio di un autista.
#
def newtrip_handler(bot, update):
    data = separate_callback_data(update.callback_query.data)
    chat_id = str(update.callback_query.message.chat_id)
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

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Scegli il giorno della settimana del viaggio.",
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

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Scegli l'ora di partenza del viaggio. ",
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

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Scegli i minuti di partenza del viaggio.",
                              reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # Metodo di conferma finale
    # Dati in entrata: "NEWTRIP", "CONFIRM", minute, hour, day, direction
    #
    elif mode == "CONFIRM":
        minute, hour, day, direction = data[2:]
        time = f"{hour.zfill(2)}:{minute.zfill(2)}"

        keyboard = [
            [InlineKeyboardButton("Indietro", callback_data=ccd("TRIPS"))],
            [InlineKeyboardButton("Esci", callback_data=ccd("EXIT"))]
        ]

        secrets.groups[direction][str(day)][str(chat_id)] = {"Time": str(time),
                                                             "Permanent": [],
                                                             "Temporary": [],
                                                             "SuspendedUsers": [],
                                                             "Suspended": False}

        user_text = f"Viaggio aggiunto con successo:" \
                    f"\n\n{common.dir_name(direction)}" \
                    f"\n🗓 {day}" \
                    f"\n🕓 {str(time)}"

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=user_text,
                              reply_markup=InlineKeyboardMarkup(keyboard))
