# -*- coding: utf-8 -*-
from telegram import InlineQueryResultArticle, InputTextMessageContent

from data.data_api import all_users, get_trip_group, get_name, get_trip
from util import common


def inline_handler(bot, update):
    query = update.inline_query.query.lower()
    chat_id = str(update.inline_query.from_user.id)
    if not query or chat_id not in all_users():
        return

    results = []

    for day in common.work_days:
        for direction in "Salita", "Discesa":
            for driver in get_trip_group(direction, day):
                driver_name = get_name(driver)
                if query in day.lower() or query in driver_name.lower():
                    # Visualizzo solo le query contenenti giorno o autista
                    trip = get_trip(direction, day, driver)
                    people = ', '.join([f"{get_name(user)}" for mode in trip
                                        if mode == "Temporary" or mode == "Permanent" for user in trip[mode]])
                    results.append(
                        InlineQueryResultArticle(
                            id=f"{direction}{day}{driver}",
                            title=f"{driver_name.split(' ')[-1]} {day} {common.dir_name(direction)}",
                            input_message_content=InputTextMessageContent(
                                f"\n\n🚗 {driver_name}"
                                f"{' - 🚫 Sospeso' if trip['Suspended'] else ''}"
                                f"\n🗓 {day}"
                                f"\n🕓 {trip['Time']}"
                                f"\n{common.dir_name(direction)}"
                                f"\n👥 {people}"
                            ),
                            hide_url=True,
                            thumb_url=common.povo_url if direction == "Salita" else common.nest_url,
                            thumb_height=40,
                            thumb_width=40
                        )
                    )

    bot.answer_inline_query(update.inline_query.id, results)
