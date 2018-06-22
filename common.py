import datetime
import time


def this_day():
    return day_to_string(datetime.datetime.today().weekday())


def next_day():
    return day_to_string(datetime.datetime.today().weekday() + 1)


def day_to_string(input):
    date = (input) % 7
    if date == 0:
        return u"Lunedi"
    elif date == 1:
        return u'Martedi'
    elif date == 2:
        return u"Mercoledi"
    elif date == 3:
        return u"Giovedi"
    elif date == 4:
        return u"Venerdi"
    elif date == 5:
        return u"Sabato"
    elif date == 6:
        return u"Domenica"


def is_today_weekday():
    return 0 <= datetime.datetime.today().weekday() <= 4


def is_tomorrow_weekday():
    return 0 <= datetime.datetime.today().weekday() + 1 <= 4


def is_dst():
    return time.localtime().tm_isdst
