# -*- coding: utf-8 -*-

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import secrets
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
        prenota_cq(bot, update)
    else:
        prenota_cmd(bot, update)


def prenota_cmd(bot, update):
    chat_id = str(update.message.chat_id)

    if chat_id in secrets.users:
        keyboard = [[InlineKeyboardButton("🔂 Prenotare una-tantum",
                                          callback_data=ccd("BOOKING", "NEW", "Temporary"))],
                    [InlineKeyboardButton("🔁 Prenotare in maniera permanente",
                                          callback_data=ccd("BOOKING", "NEW", "Permanent"))],
                    [InlineKeyboardButton("📚 Gestire le mie prenotazioni",
                                          callback_data=ccd("EDIT_BOOK", "LIST"))],
                    [InlineKeyboardButton("🔚 Uscire", callback_data=ccd("EXIT"))]]

        bot.send_message(chat_id=chat_id,
                         text="Cosa vuoi fare?",
                         reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        bot.send_message(chat_id=chat_id,
                         text="Per effettuare una prenotazione, registrati con /registra.")


def prenota_cq(bot, update):
    chat_id = str(update.callback_query.from_user.id)

    keyboard = [[InlineKeyboardButton("🔂 Prenotare una-tantum",
                                      callback_data=ccd("BOOKING", "NEW", "Temporary"))],
                [InlineKeyboardButton("🔁 Prenotare in maniera permanente",
                                      callback_data=ccd("BOOKING", "NEW", "Permanent"))],
                [InlineKeyboardButton("📚 Gestire le mie prenotazioni",
                                      callback_data=ccd("EDIT_BOOK", "LIST"))],
                [InlineKeyboardButton("🔚 Uscire", callback_data=ccd("EXIT"))]]

    bot.edit_message_text(chat_id=chat_id,
                          message_id=update.callback_query.message.message_id,
                          text="Cosa vuoi fare?",
                          reply_markup=InlineKeyboardMarkup(keyboard))


def booking_handler(bot, update):
    """
    Gestore dei metodi delle prenotazioni. Da questo menù è possibile aggiungere prenotazioni.
    """
    data = separate_callback_data(update.callback_query.data)
    action = data[1]
    chat_id = str(update.callback_query.message.chat_id)

    #
    # Dati in entrata ("BOOKING", "NEW", mode)
    # Questo metodo viene automaticamente chiamato con la modalità preselezionata. I viaggi mostrati sono
    # comunque uguali e differiscono solo per la callback_query a loro assegnata. Il messaggio di avviso invece
    # cambia a seconda della modalità scelta. Infine, il menù è limitato a un uso entro un range orario definito
    # in common.py per evitare prenotazioni notturne assurde.
    #
    if action == "NEW":
        if common.is_booking_time():
            mode = data[2]

            if mode == "Temporary":
                text = "Si ricorda che le prenotazioni una-tantum vengono automaticamente cancellate ed" \
                       " addebitate il giorno dopo la prenotazione. E' possibile prenotarsi a un viaggio" \
                       " già avvenuto, ma verrà addebitato comunque."
            elif mode == "Permanent":
                text = "Si ricorda che le prenotazioni permanenti verranno addebitate anche per i viaggi" \
                       " prenotati per la giornata corrente."
            else:
                text = ""

            user_keyboard = [
                [InlineKeyboardButton(day[:2],  # Abbreviazione del giorno
                                      callback_data=ccd("BOOKING", "DAY", mode, day))
                 for day in common.work_days],
                [InlineKeyboardButton("↩ Indietro", callback_data=ccd("BOOKING_MENU"))],
                [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
            ]

            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=f"{text}\n\nScegli la data della prenotazione.",
                                  reply_markup=InlineKeyboardMarkup(user_keyboard))
        else:
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text=f"Mi dispiace, è possibile effettuare prenotazioni"
                                       f" tramite UberNEST solo dalle "
                                       f"{common.booking_start.strftime('%H:%M')}"
                                       f" alle {common.booking_end.strftime('%H:%M')}.")
    #
    # Dati in entrata ("BOOKING", "DAY", mode, day)
    # Questo menù viene chiamato rispettivamente dal metodo sopra (BOOKING/NEW) e dai visualizzatori
    # delle prenotazioni dei singoli giorni (/lunedi, /martedi, etc...).
    elif action == "DAY":
        mode, day = data[2:4]
        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=f"Viaggi disponibili per {day.lower()}:",
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
            [InlineKeyboardButton("↩ Indietro", callback_data=ccd("BOOKING", "DAY", mode, day))],
            [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
        ]

        trip = secrets.groups[direction][day][driver]
        occupied_slots = len(trip["Permanent"]) + len(trip["Temporary"])
        total_slots = secrets.drivers[driver]["Slots"]

        # Caso in cui l'autista tenta inutilmente di prenotarsi con sè stesso...
        if chat_id == driver:
            user_text = "Sei tu l'autista!"

        # Caso in cui tutti gli slot sono occupati
        elif occupied_slots >= total_slots:
            user_text = "Macchina piena, vai a piedi LOL. 🚶🏻‍♂️"

        # Caso in cui lo stolto passeggero si era già prenotato
        elif chat_id in trip["Temporary"] or chat_id in trip["Permanent"] or chat_id in trip["SuspendedUsers"]:
            user_text = "Ti sei già prenotato in questa data con questa persona!"

        else:
            # Si attende conferma dall'autista prima di aggiungere
            trip_time = trip["Time"]
            slots = str(total_slots - occupied_slots - 1)

            if "Location" in trip:
                location = trip["Location"]
                user_keyboard.insert(0, [InlineKeyboardButton("📍 Mostra sulla mappa",
                                                              callback_data=ccd("SEND_LOCATION", location))])
            elif direction == "Salita":
                location = "Macchinette"
            else:
                location = "Non definita"

            driver_keyboard = [
                [InlineKeyboardButton("✔ Conferma",
                                      callback_data=ccd("ALERT_USER", "CO_BO", direction, day, chat_id, mode))]
            ]

            user_text = f"Prenotazione completata. Dati del viaggio:" \
                        f"\n\n🚗: [{secrets.users[driver]['Name']}](tg://user?id={driver})" \
                        f"\n🗓 {day}" \
                        f"\n🕓 {trip_time}" \
                        f"\n{common.dir_name(direction)}" \
                        f"\n{common.mode_name(mode)}" \
                        f"\n📍 {location}" \
                        f"\n\nLa prenotazione sarà resa valida al momento della conferma dall'autista."

            driver_text = "Hai una nuova prenotazione: " \
                          f"\n\n👤: [{secrets.users[chat_id]['Name']}](tg://user?id={chat_id}) " \
                          f"({slots} posti rimanenti)" \
                          f"\n🗓 {day}" \
                          f"\n🕓 {trip_time}" \
                          f"\n{common.dir_name(direction)}" \
                          f"\n{common.mode_name(mode)}" \
                          f".\n\nPer favore, conferma la presa visione della prenotazione. In caso negativo," \
                          f" la prenotazione verrà considerata non valida."

            bot.send_message(chat_id=driver,
                             text=driver_text,
                             reply_markup=InlineKeyboardMarkup(driver_keyboard),
                             parse_mode="Markdown")

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=user_text,
                              reply_markup=InlineKeyboardMarkup(user_keyboard),
                              parse_mode="Markdown")


def edit_booking(bot, update):
    """
    Questo metodo viene chiamato al momento della richiesta di visione della lista delle prenotazioni da 
    parte dell'utente. Le prenotazione vengono prese tramite query dal metodo search_by_booking presente
    in common.py. Dal menù, una volta selezionata una prenotazione, è possibile cancellarla oppure sospenderla
    a lato utente, ovvero bloccarla per una settimana.
    """
    chat_id = str(update.callback_query.message.chat_id)
    data = separate_callback_data(update.callback_query.data)
    action = data[1]

    #
    #  Comando base chiamato dal metodo prenota. Effettua una query di tutti i viaggi presentandoli
    #  sottoforma di bottoni all'utente.
    #
    if action == "LIST":
        bookings = common.get_bookings(chat_id)

        keyboard = [
            [InlineKeyboardButton("↩ Indietro", callback_data=ccd("BOOKING_MENU"))],
            [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
        ]

        if len(bookings) > 0:
            user_keyboard = []

            for item in bookings:
                direction, day, driver, mode, time = item
                driver_name = secrets.users[driver]["Name"]

                if secrets.groups[direction][day][driver]["Suspended"]:
                    tag = " 🚫 Sospesa"
                else:
                    tag = f" 🗓 {day} 🕓 {time}"

                # Aggiunta del bottone
                user_keyboard.append([InlineKeyboardButton(
                    f"🚗 {driver_name.split(' ')[-1]}{tag}\n{common.dir_name(direction)} {common.mode_name(mode)}",
                    callback_data=ccd("EDIT_BOOK", "ACTION", direction, day, driver, mode))])

            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text="Clicca su una prenotazione per cancellarla o sospenderla.",
                                  reply_markup=InlineKeyboardMarkup(user_keyboard + keyboard))
        else:
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=update.callback_query.message.message_id,
                                  text="Mi dispiace, ma non hai prenotazioni all'attivo.",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    #
    # Menù disponibile all'utente una volta selezionato un viaggio. I bottoni cambiano a seconda della prenotazione:
    # Temporanea -> solo cancellazione
    # Permanente e sospesa -> sospensione e cancellazione
    #
    elif action == "ACTION":
        direction, day, driver, mode = data[2:]
        keyboard = [
            [InlineKeyboardButton("❌ Annulla prenotazione",
                                  callback_data=ccd("EDIT_BOOK", "DELETION", direction, day, driver, mode))],
            [InlineKeyboardButton("↩ Indietro", callback_data=ccd("EDIT_BOOK", "LIST"))],
            [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
        ]

        text_string = []
        trip_time = secrets.groups[direction][day][driver]["Time"]

        if mode == "Permanent":
            keyboard.insert(0, [InlineKeyboardButton(
                "Sospendi prenotazione",
                callback_data=ccd("EDIT_BOOK", "SUS_BOOK", direction, day, driver, mode))])

        elif mode == "SuspendedUsers":
            text_string.append(" - SOSPESA dall'utente")
            keyboard.insert(0, [InlineKeyboardButton(
                "Annulla sospensione prenotazione",
                callback_data=ccd("EDIT_BOOK", "SUS_BOOK", direction, day, driver, mode))])

        if secrets.groups[direction][day][driver]["Suspended"]:
            text_string.append(" - SOSPESA dall'autista")

        text_string = "".join(text_string)

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=f"Prenotazione selezionata: {text_string}\n"
                                   f"\n🚗 [{secrets.users[driver]['Name']}](tg://user?id={driver})"
                                   f"\n🗓 {day}"
                                   f"\n{common.dir_name(direction)}"
                                   f"\n🕓 {trip_time}"
                                   f"\n{common.mode_name(mode)}",
                              reply_markup=InlineKeyboardMarkup(keyboard),
                              parse_mode="Markdown")
    #
    # SUS_BOOK = SUSPEND_BOOKING
    #
    elif action == "SUS_BOOK":
        booking = data[2:]
        mode = booking[3]

        keyboard = [
            InlineKeyboardButton("✔ Sì", callback_data=ccd("EDIT_BOOK", "CO_SUS_BOOK", *booking)),
            InlineKeyboardButton("❌ No", callback_data=ccd("EDIT_BOOK", "LIST"))
        ]

        if mode == "Permanent":
            message = "Si ricorda che la sospensione di una prenotazione è valida per una sola settimana." \
                      "\n\nSei sicuro di voler sospendere questo viaggio?"

        elif mode == "SuspendedUsers":
            message = "Vuoi rendere di nuovo operativa questa prenotazione?"

        else:
            message = "Errore fatale nel Bot. Contatta il creatore del bot al più presto."

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=message,
                              reply_markup=InlineKeyboardMarkup([keyboard]))
    #
    # CO_SUS_BOOK = CONFIRM_SUSPEND_BOOKING
    # Il metodo scambia la chiave di un utente da Permanente a SuspendUsers e vice-versa.
    #
    elif action == "CO_SUS_BOOK":
        direction, day, driver, mode = data[2:]
        trip = secrets.groups[direction][day][driver]

        keyboard = [
            [InlineKeyboardButton("↩ Indietro", callback_data=ccd("EDIT_BOOK", "LIST"))],
            [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
        ]

        if mode == "Permanent":
            trip["Permanent"].remove(chat_id)
            trip["SuspendedUsers"].append(chat_id)

            user_message = "Prenotazione sospesa. Verrà ripristinata il prossimo viaggio."
            driver_message = f"[{secrets.users[chat_id]['Name']}](tg://user?id={chat_id})" \
                             f" ha sospeso la sua prenotazione permanente" \
                             f" per {day.lower()} {common.dir_name(direction)}."

        elif mode == "SuspendedUsers":
            occupied_slots = len(trip["Permanent"]) + len(trip["Temporary"])
            total_slots = secrets.drivers[driver]["Slots"]

            if occupied_slots >= total_slots:
                # Può capitare che mentre un passeggero ha reso la propria prenotazione sospesa,
                # altre persone hanno preso il suo posto.
                bot.edit_message_text(chat_id=chat_id,
                                      message_id=update.callback_query.message.message_id,
                                      text=f"Mi dispiace, ma non puoi rendere operativa la"
                                           f" tua prenotazione in quanto la macchina è ora piena."
                                           f"Contatta [{secrets.users[driver]['Name']}](tg://user?id={driver})"
                                           f" per risolvere la questione.",
                                      reply_markup=InlineKeyboardMarkup(keyboard),
                                      parse_mode="Markdown")
                return

            trip["Permanent"].append(chat_id)
            trip["SuspendedUsers"].remove(chat_id)

            user_message = "La prenotazione è di nuovo operativa."
            driver_message = f"[{secrets.users[chat_id]['Name']}](tg://user?id={chat_id})" \
                             f" ha reso operativa la sua prenotazione permanente" \
                             f" di {day.lower()} {common.dir_name(direction)}."

        else:
            user_message = "Errore fatale nel Bot. Contatta il creatore del bot al più presto."
            driver_message = "Errore: un tuo passeggero ha cercato di sospendere " \
                             "una prenotazione temporanea. Contatta il creatore del bot al più presto."

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text=user_message,
                              reply_markup=InlineKeyboardMarkup(keyboard),
                              parse_mode="Markdown")
        bot.send_message(chat_id=driver, text=driver_message,
                         parse_mode="Markdown")
    #
    # Metodo per cancellare per sempre una data prenotazione.
    #
    elif action == "DELETION":
        booking = data[2:]

        keyboard = [
            InlineKeyboardButton("✔ Sì", callback_data=ccd("EDIT_BOOK", "CO_DEL", *booking)),
            InlineKeyboardButton("❌ No", callback_data=ccd("EDIT_BOOK", "LIST"))
        ]

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Sei sicuro di voler cancellare questo viaggio?",
                              reply_markup=InlineKeyboardMarkup([keyboard]))
    #
    # CO_DEL = CONFIRM_DELETION
    #
    elif action == "CO_DEL":
        direction, day, driver, mode = data[2:]
        secrets.groups[direction][day][driver][mode].remove(chat_id)

        keyboard = [
            [InlineKeyboardButton("↩ Indietro", callback_data=ccd("EDIT_BOOK", "LIST"))],
            [InlineKeyboardButton("🔚 Esci", callback_data=ccd("EXIT"))]
        ]

        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              text="Prenotazione cancellata con successo.",
                              reply_markup=InlineKeyboardMarkup(keyboard))
        bot.send_message(chat_id=driver,
                         text=f"Una prenotazione al tuo viaggio è stata cancellata:"
                              f"\n\n👤 [{secrets.users[chat_id]['Name']}](tg://user?id={chat_id})"
                              f"\n🗓 {day}"
                              f"\n{common.dir_name(direction)}",
                         parse_mode="Markdown")


def alert_user(bot, update):
    chat_id = str(update.callback_query.message.chat_id)
    data = separate_callback_data(update.callback_query.data)
    action = data[1]

    if action == "CO_BO":
        direction, day, user, mode = data[2:]  # Utente della prenotazione

        trip = secrets.groups[direction][day][chat_id]
        occupied_slots = len(trip["Permanent"]) + len(trip["Temporary"])
        total_slots = secrets.drivers[chat_id]["Slots"]

        if occupied_slots < total_slots:
            if user not in trip[mode]:
                trip[mode].append(user)
                edited_text = "Hai una nuova prenotazione: " \
                              f"\n\n👤: [{secrets.users[user]['Name']}](tg://user?id={user}) ✔" \
                              f"(*{total_slots - occupied_slots - 1} posti rimanenti*)" \
                              f"\n🗓 {day}" \
                              f"\n🕓 {secrets.groups[direction][day][chat_id]['Time']}" \
                              f"\n{common.dir_name(direction)}" \
                              f"\n{common.mode_name(mode)}" \
                              f".\n\nPrenotazione confermata con successo."
                booker_text = f"[{secrets.users[chat_id]['Name']}](tg://user?id={chat_id})" \
                              f" ha confermato la tua prenotazione."
            else:
                edited_text = "⚠ Attenzione, questa persona è già prenotata con te in questo viaggio."
                booker_text = "⚠ Ti sei già prenotato in questa data con questa persona!"
        else:
            edited_text = "⚠ Attenzione, hai esaurito i posti disponibili per questo viaggio. Non è" \
                          " possibile confermarlo."
            booker_text = f"⚠ Mi dispiace, ma qualcun'altro si è prenotato prima di te. Contatta " \
                          f"[{secrets.users[chat_id]['Name']}](tg://user?id={chat_id}) per disponibilità posti."

        bot.send_message(chat_id=user, parse_mode="Markdown", text=booker_text)
        bot.edit_message_text(chat_id=chat_id,
                              message_id=update.callback_query.message.message_id,
                              parse_mode="Markdown",
                              reply_markup=None,
                              text=edited_text)
