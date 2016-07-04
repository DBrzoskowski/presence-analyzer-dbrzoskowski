# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
from __future__ import unicode_literals

import datetime
import json
import os.path
import unittest
from time import time

import main
import utils
import views


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)
TEST_XML_DATA = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_users.xml'
)

# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):

    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'XML_DATA': TEST_XML_DATA})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_xml_data(self):
        resp = self.client.get('/api/v2/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertDictEqual(data[0], {
            'name': 'Kamil K.',
            'user_id': 16,
            'avatar': 'https://intranet.stxnext.pl/api/images/users/16'
        })

    def test_mean_time_weekend(self):
        """
        Test mean time weekend.
        """
        resp = self.client.get('/api/v2/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        expected_list = [
            ['Mon', 23705.0],
            ['Tue', 30047.0],
            ['Wed', 24465.0],
            ['Thu', 0],
            ['Fri', 0],
            ['Sat', 0],
            ['Sun', 0]
        ]
        self.assertEqual(data, expected_list)
        self.assertEqual(data[0], expected_list[0])
        self.assertEqual(data[-1], expected_list[-1])

    def test_presence_weekday_view(self):
        """
        Test presence weekday.
        """
        resp = self.client.get('/api/v2/presence_weekday/11')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        expected_list = [
            ['Weekday', 'Presence (s)'],
            ['Mon', 30549],
            ['Tue', 16564],
            ['Wed', 25321],
            ['Thu', 45968],
            ['Fri', 0],
            ['Sat', 0],
            ['Sun', 0]
        ]
        self.assertEqual(data, expected_list)
        self.assertEqual(data[0], expected_list[0])
        self.assertEqual(data[-1], expected_list[-1])

    def test_presence_start_end(self):
        """
        Test start and end time of given user grouped by weekday.
        """
        resp = self.client.get('/api/v2/presence_start_end/11')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        expected_list = [
            ['Mon', 40475.0, 55749.5],
            ['Tue', 33590.0, 50154.0],
            ['Wed', 33206.0, 58527.0],
            ['Thu', 35602.0, 58586.0],
            ['Fri', 0, 0],
            ['Sat', 0, 0],
            ['Sun', 0, 0]
        ]
        self.assertEqual(data, expected_list)
        self.assertEqual(data[0], expected_list[0])
        self.assertEqual(data[-1], expected_list[-1])

    def test_presence_top5(self):
        """
        Test presence top5.
        """
        resp = self.client.get("/api/v2/presence_top5/29-4-2013")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        expected_list = [
            ['Marek B.', 0, 30878.0],
            ['Adam P.', 0, 29067.0],
            ['Marek P.', 0, 28808.0],
            ['Kamil K.', 0, 20843.0],
            ['Kajetan O.', 0, 3414.0]
        ]
        self.assertEqual(data, expected_list)
        self.assertEqual(data[0], expected_list[0])
        self.assertEqual(data[-1], expected_list[-1])


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'XML_DATA': TEST_XML_DATA})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_cache(self):
        """
        Test cache decorator for get_data function.
        """
        CACHE = utils.CACHE
        self.assertEqual(CACHE, {})
        data = utils.get_data()
        self.assertNotEqual(CACHE, {})
        self.assertEqual(CACHE['get_data']['data'], data)
        cache_time = CACHE['get_data']['time']
        CACHE['get_data']['time'] = time() + 86400
        utils.get_data()
        self.assertNotEqual(cache_time, CACHE['get_data']['time'])
        CACHE = {}

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [130, 10, 11, 141, 16, 20, 23])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_xml_data_parser(self):
        """
        Test xml data parser.
        """
        data = utils.xml_data_parser()
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data.keys()[0], int)
        self.assertEqual(
            data[141], {
                'name': 'Adam P.',
                'avatar': 'https://intranet.stxnext.pl/api/images/users/141'
            }
        )

    def test_group_by_weekday(self):
        """
        Test group by weekend.
        """
        excepted_result = [[], [0], [17088], [10800], [], [], []]
        days = {
            datetime.date(2013, 9, 10): {
                'end': datetime.time(0, 0, 0),
                'start': datetime.time(0, 0, 0),
            },
            datetime.date(2013, 9, 11): {
                'end': datetime.time(17, 6, 28),
                'start': datetime.time(12, 21, 40),
            },
            datetime.date(2013, 9, 12): {
                'end': datetime.time(23, 59, 59),
                'start': datetime.time(20, 59, 59),
            }
        }
        data = utils.group_by_weekday(days)
        self.assertEqual(data, excepted_result)
        self.assertTrue(
            datetime.datetime.strptime(
                str(datetime.date(2013, 9, 12)), '%Y-%m-%d'
            )
        )

    def test_group_by_start_end(self):
        """
        Test group by start, end.
        """
        excepted_result = {
            0: {'end': [], 'start': []},
            1: {'end': [79254, 61588], 'start': [41580, 44500]},
            2: {'end': [47188, 75988], 'start': [19300, 44500]},
            3: {'end': [79199, 86399], 'start': [28169, 75599]},
            4: {'end': [], 'start': []},
            5: {'end': [], 'start': []},
            6: {'end': [], 'start': []}
        }
        days = {
            datetime.date(2013, 9, 10): {
                'end': datetime.time(22, 0, 54),
                'start': datetime.time(11, 33, 0),
            },
            datetime.date(2013, 9, 17): {
                'end': datetime.time(17, 6, 28),
                'start': datetime.time(12, 21, 40),
            },
            datetime.date(2013, 9, 11): {
                'end': datetime.time(13, 6, 28),
                'start': datetime.time(5, 21, 40),
            },
            datetime.date(2013, 9, 18): {
                'end': datetime.time(21, 6, 28),
                'start': datetime.time(12, 21, 40),
            },
            datetime.date(2013, 9, 12): {
                'end': datetime.time(21, 59, 59),
                'start': datetime.time(7, 49, 29),
            },
            datetime.date(2013, 9, 19): {
                'end': datetime.time(23, 59, 59),
                'start': datetime.time(20, 59, 59),
            }
        }
        data = utils.group_by_start_end(days)
        self.assertEqual(data, excepted_result)

    def test_seconds_since_midnight(self):
        """
        Test calculates amount of seconds since midnight.
        """
        sample_date = datetime.time(18, 17, 4)
        date = (
            utils.seconds_since_midnight(
                datetime.time(23, 11, 0)
            ),
            utils.seconds_since_midnight(
                datetime.time(0, 0, 0)
            ),
            utils.seconds_since_midnight(
                datetime.time(5, 54, 43)
            ),
        )
        self.assertLess(sample_date.hour, 24)
        self.assertGreater(sample_date.hour, -1)
        self.assertLess(sample_date.minute, 60)
        self.assertGreater(sample_date.minute, -1)
        self.assertLess(sample_date.second, 60)
        self.assertGreater(sample_date.second, -1)
        self.assertEqual(date[0], 83460)
        self.assertEqual(date[1], 0)
        self.assertEqual(date[2], 21283)

    def test_interval(self):
        """
        Test interval between two datetime.time objects.
        """
        date = (
            utils.interval(
                datetime.time(8, 31, 6),
                datetime.time(15, 15, 27),
            ),
            utils.interval(
                datetime.time(0, 0, 0),
                datetime.time(0, 0, 0),
            ),
            utils.interval(
                datetime.time(5, 30, 5),
                datetime.time(10, 15, 53),
            ),
        )
        self.assertEqual(date[0], 24261)
        self.assertEqual(date[1], 0)
        self.assertEqual(date[2], 17148)

    def test_mean(self):
        """
        Test calculates arithmetic mean.
        """
        date = (
            utils.mean([24261, 32533, 34323, 32453, 54154, 32412, 31123]),
            utils.mean([0]),
            utils.mean([-12332, -3213, -3213, -32131, -32131])
        )
        self.assertEqual(date[0], 34465.57142857143)
        self.assertEqual(date[1], 0)
        self.assertEqual(date[2], -16604)

    def test_date_set(self):
        """
        Test list set unique dates
        """
        test_data = {
            177: {
                datetime.date(2013, 9, 9): {
                    'end': datetime.time(16, 51, 44),
                    'start': datetime.time(9, 21, 59)
                },
                datetime.date(2013, 9, 10): {
                    'end': datetime.time(16, 55, 7),
                    'start': datetime.time(8, 47, 52)
                },
                datetime.date(2013, 9, 11): {
                    'end': datetime.time(16, 52, 44),
                    'start': datetime.time(8, 51, 11)
                },
                datetime.date(2013, 9, 12): {
                    'end': datetime.time(16, 36, 2),
                    'start': datetime.time(8, 35, 42)
                }
            },
            178: {
                datetime.date(2013, 9, 9): {
                    'end': datetime.time(17, 14, 42),
                    'start': datetime.time(11, 43, 50)
                },
                datetime.date(2013, 9, 10): {
                    'end': datetime.time(19, 0, 12),
                    'start': datetime.time(8, 59, 59)
                },
                datetime.date(2013, 9, 11): {
                    'end': datetime.time(17, 2, 37),
                    'start': datetime.time(9, 1, 26)
                },
                datetime.date(2013, 9, 12): {
                    'end': datetime.time(17, 3, 8),
                    'start': datetime.time(8, 59, 59)
                }
            },
            179: {
                datetime.date(2013, 9, 12): {
                    'end': datetime.time(18, 5, 24),
                    'start': datetime.time(16, 55, 24)
                }
            }
        }
        data = utils.date_set(test_data)
        date = datetime.date(2013, 9, 12)
        self.assertIsInstance(data, list)
        self.assertEqual(data[1], date)
        self.assertNotEqual(data[0], date)

    def test_dates_parser(self):
        """
        Test dict unique dates and values user_id, work spend time.
        """
        data = utils.dates_parser()
        date = datetime.date(2013, 4, 29)
        self.assertIsInstance(data, dict)
        self.assertEqual(data[date], {
            16: 20843.0,
            130: 3414.0,
            20: 28808.0,
            141: 29067.0,
            23: 30878.0
            }
        )
        self.assertIsInstance(data[date][130], float)

    def test_top5_users(self):
        data = utils.top5_users(datetime.date(2013, 4, 29))
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)
        self.assertEqual(data, [
            (23, 30878.0),
            (141, 29067.0),
            (20, 28808.0),
            (16, 20843.0),
            (130, 3414.0)
            ]
        )
        self.assertIsInstance(data[0][1], float)


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
