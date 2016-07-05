# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import logging
import os
import threading
import urllib2

from datetime import datetime
from functools import wraps
from json import dumps
from time import time

from flask import Response
from lxml import etree

from main import app


log = logging.getLogger(__name__)  # pylint: disable=invalid-name
CACHE = {}


def lock(function):
    """
    Lock function decorator.
    """
    locked = threading.Lock()
    @wraps(function)
    def locking(*args, **kwargs):
        with locked:
            result = function(*args, **kwargs)
        return result
    return locking


def cache(cache_time):
    """
    Cache function decorator with cache time as argument.
    """
    def _cache(function):
        def __cache(*args, **kwargs):
            name = function.__name__
            if name in CACHE:
                if CACHE[name]['time'] < time() + cache_time:
                    return CACHE[name]['data']
            CACHE[name] = {
                'data': function(*args, **kwargs),
                'time': time()
            }
            return CACHE[name]['data']
        return __cache
    return _cache


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


@lock
@cache(600)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue
            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)
            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}
    return data


@lock
@cache(600)
def xml_data_parser():
    """
    Parse data from xml file.
    """
    with open(app.config['XML_DATA'], 'r') as users:
        tree = etree.parse(users)
        users = tree.find('users')
        server = tree.find('server')
        host = server.find('host').text
        protocol = server.find('protocol').text
        data = {
            int(user.get('id')): {
                'avatar': '{protocol}://{host}{user}'.format(
                    protocol=protocol,
                    host=host,
                    user=user.find('avatar').text
                ),
                'name': user.find('name').text
            }
            for user in users.findall('user')
        }
    return data


def xml_update_data():
    """
    Update data from xml file.
    """
    with open(app.config['XML_DATA'], 'w') as file:
        response = urllib2.urlopen(app.config['UPDATE_XML_DATA'])
        html = response.read()
        file.write(html)


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def group_by_start_end(items):
    """
    Groups entries by weekday for start and end.
    """
    result = {i: {'start': [], 'end': []} for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()]['start'].append(
            seconds_since_midnight(start)
        )
        result[date.weekday()]['end'].append(
            seconds_since_midnight(end)
        )
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def group_by_spend_time(items):
    """
    User spend time in work for date.
    """
    result = {}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.strftime("%d-%m-%Y")] = interval(start, end)
    return result


def top5_dates(items):
    """
    Group top5 dates for user.
    """
    dates = group_by_spend_time(items)
    return sorted(
        dates.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

