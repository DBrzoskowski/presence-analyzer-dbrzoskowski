# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import datetime
import logging

from flask import abort, make_response, redirect, render_template
from flask.ext.mako import render_template
from jinja2.exceptions import TemplateNotFound

from main import app
from utils import (
    get_data,
    group_by_spend_time,
    group_by_start_end,
    group_by_weekday,
    jsonify,
    mean,
    seconds_since_midnight,
    top5_dates,
    xml_data_parser
)


log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/<string:templates_name>/', methods=['GET'])
def render_templates(templates_name):
    """
    Render view for .html file.
    """
    if not templates_name.endswith('.html'):
        templates_name = '{}.html'.format(templates_name)
    try:
        return render_template(templates_name, templates_name=templates_name)
    except TemplateNotFound:
        return make_response("page not found", 404)


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/presence_weekday.html')


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@app.route('/api/v2/users', methods=['GET'])
@jsonify
def xml_data_view():
    """
    Loading data from xml_data_parser for users.
    """
    data = xml_data_parser()
    return [
        {
            'user_id': i,
            'name': data[i]['name'],
            'avatar': data[i]['avatar']
        }
        for i in data
    ]


@app.route('/api/v2/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]
    return result


@app.route('/api/v2/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]
    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v2/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns start and end time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    start_end_weekdays = group_by_start_end(data[user_id])
    result = [(
        calendar.day_abbr[weekday],
        mean(start_end_weekdays[weekday]['start']),
        mean(start_end_weekdays[weekday]['end']))
        for weekday, intervals in enumerate(weekdays)
    ]
    return result


@app.route('/api/v2/user_top5_dates/<int:user_id>', methods=['GET'])
@jsonify
def presence_top5_dates_view(user_id):
    """
    Returns top5 dates for user.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    top_5 = top5_dates(data[user_id])
    result = [(
        date[0], 0, date[1])
        for date in top_5
    ]
    return result

