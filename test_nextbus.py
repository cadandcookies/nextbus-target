import datetime
import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests

from nextbus import NextBus


class NextBusFunctionalTest(TestCase):
    def setUp(self):
        self.nextbus = NextBus()
        self.nextbus.log.error = MagicMock()

    def test_run_all_valid(self):
        with patch('builtins.print') as print_mock:
            self.nextbus.run(arguments=["5 - Brooklyn Ctr", "Mall of America", "north"])
            print_mock.assert_called()
            self.nextbus.log.error.assert_not_called()

    def test_run_invalid_route(self):
        with patch('builtins.print') as print_mock:
            self.nextbus.run(arguments=["lol", "Mall of America", "north"])
            print_mock.assert_not_called()
            self.nextbus.log.error.assert_called()
            call_args = self.nextbus.log.error.call_args_list
            assert "No valid route for lol. Valid routes are:" in call_args[0][0][0]

    def test_run_invalid_route_ambiguous(self):
        with patch('builtins.print') as print_mock:
            self.nextbus.run(arguments=["5", "Mall of America", "north"])
            print_mock.assert_not_called()
            call_args = self.nextbus.log.error.call_args_list
            assert "Route 5 was ambiguous, matches:" in call_args[0][0][0]

    def test_run_invalid_direction(self):
        with patch('builtins.print') as print_mock:
            self.nextbus.run(arguments=["5 - Brooklyn Ctr", "Mall of America", "east"])
            print_mock.assert_not_called()
            self.nextbus.log.error.assert_called_with(
                "east is not a valid direction. Valid directions for route 5 are: ['north', 'south']"
            )

    def test_run_invalid_direction_wrong(self):
        with patch('builtins.print') as print_mock:
            self.nextbus.run(arguments=["5 - Brooklyn Ctr", "Mall of America", "lol"])
            print_mock.assert_not_called()
            call_args = self.nextbus.log.error.call_args_list
            assert (
                "lol is not a valid direction. Valid directions are:"
                in call_args[0][0][0]
            )

    def test_run_invalid_stop(self):
        with patch('builtins.print') as print_mock:
            self.nextbus.run(arguments=["5 - Brooklyn Ctr", "adwds", "north"])
            print_mock.assert_not_called()
            call_args = self.nextbus.log.error.call_args_list
            assert "No valid stop for adwds. Valid stops are:" in call_args[0][0][0]

    def test_run_invalid_stop_ambiguous(self):
        with patch('builtins.print') as print_mock:
            self.nextbus.run(arguments=["5 - Brooklyn Ctr", "a", "north"])
            print_mock.assert_not_called()
            call_args = self.nextbus.log.error.call_args_list
            assert "Route a was ambiguous, matches: " in call_args[0][0][0]


class NextBusGetTests(TestCase):
    def setUp(self):
        self.nextbus = NextBus()

    def test_get_request_exception(self):
        with patch('requests.get') as req_get:
            req_get.side_effect = requests.RequestException()
            routes = self.nextbus.get(self.nextbus.ALL_ROUTES_URL)
        assert not routes

    def test_get_json_exception(self):
        with patch('requests.get') as req_get:
            req_get.side_effect = json.decoder.JSONDecodeError(
                msg="Test", doc='{"name": "fake"}', pos=1
            )
            routes = self.nextbus.get(self.nextbus.ALL_ROUTES_URL)
        assert not routes


class NextBusUnitTests(TestCase):
    def setUp(self):
        self.nextbus = NextBus()
        self.nextbus.get = MagicMock(
            side_effect=Exception("There should be no get calls in these tests!")
        )

    # Run tests

    def setUpRunTests(self):
        self.valid_routes = [
            {'description': "Blue Line", 'number': 1},
            {'description': "Green Line", 'number': 2},
            {'description': "Red Line", 'number': 3},
        ]
        self.nextbus.get_valid_routes_for_name = MagicMock(
            return_value=[{'description': "Blue Line", 'number': 1}]
        )
        self.nextbus.get_all_routes = MagicMock(return_value=self.valid_routes)
        self.nextbus.is_valid_direction = MagicMock(return_value=True)
        self.nextbus.get_valid_stops_for_route = MagicMock(
            return_value=[{'text': "Real Stop", 'value': '1337'}]
        )
        self.valid_stops = [{'Text': "Real Stop"}, {'Text': "Fake Stop"}]
        self.nextbus.get_route_stops = MagicMock(return_value=self.valid_stops)
        self.nextbus.get_time_remaining = MagicMock(
            return_value=datetime.timedelta(seconds=360)
        )

    def test_run_success(self):
        self.setUpRunTests()
        with patch('builtins.print') as print_mock:
            self.nextbus.run(['Blue', 'Real', 'north'])
            print_mock.assert_called_with("6.0 minutes")

    def test_run_invalid_route(self):
        self.setUpRunTests()
        self.nextbus.get_valid_routes_for_name = MagicMock(return_value=[])
        with patch('builtins.print') as print_mock:
            self.nextbus.run(['Orange', 'Real', 'north'])
            print_mock.assert_not_called()

    def test_run_ambiguous_route(self):
        self.setUpRunTests()
        self.nextbus.get_valid_routes_for_name = MagicMock(
            return_value=self.valid_routes
        )
        with patch('builtins.print') as print_mock:
            self.nextbus.run(['Line', 'Real', 'north'])
            print_mock.assert_not_called()

    def test_run_invalid_direction(self):
        self.setUpRunTests()
        self.nextbus.is_valid_direction = MagicMock(return_value=False)
        with patch('builtins.print') as print_mock:
            self.nextbus.run(['Line', 'Real', 'no'])
            print_mock.assert_not_called()

    def test_run_invalid_stop(self):
        self.setUpRunTests()
        self.nextbus.get_valid_stops_for_route = MagicMock(return_value=[])
        with patch('builtins.print') as print_mock:
            self.nextbus.run(['Line', 'Real', 'north'])
            print_mock.assert_not_called()

    def test_run_ambiguous_stop(self):
        self.setUpRunTests()
        self.nextbus.get_valid_stops_for_route = MagicMock(
            return_value=self.valid_stops
        )
        with patch('builtins.print') as print_mock:
            self.nextbus.run(['Line', 'Stop', 'north'])
            print_mock.assert_not_called()

    def test_run_bad_time(self):
        self.setUpRunTests()
        self.nextbus.get_time_remaining = MagicMock(return_value=datetime.timedelta(-1))
        with patch('builtins.print') as print_mock:
            self.nextbus.run(['Line', 'Stop', 'north'])
            print_mock.assert_not_called()

    # Cache tests

    def test_cache_hit(self):
        self.nextbus.cache.update({'test': 'stuff'})
        assert 'stuff' == self.nextbus._NextBus__cache('test', 'fakeurl')

    def test_cache_miss(self):
        self.nextbus.get = MagicMock(return_value="stuff")
        assert 'stuff' == self.nextbus._NextBus__cache('test', 'fakeurl')
        assert {'test': 'stuff'} == self.nextbus.cache

    def test_cache_force_reset(self):
        self.nextbus.cache.update({'test': 'stuff'})
        self.nextbus.get = MagicMock(return_value="lol")
        assert 'lol' == self.nextbus._NextBus__cache('test', 'fakeurl', True)
        assert {'test': 'lol'} == self.nextbus.cache

    def test_cache_no_return(self):
        self.nextbus.get = MagicMock(return_value=[])
        assert [] == self.nextbus._NextBus__cache('test', 'fakeurl')
        assert not self.nextbus.cache

    # is_valid_direction tests

    def test_is_valid_direction_true(self):
        self.nextbus.get_route_directions = MagicMock(
            return_value=[{'Value': '4'}, {'Value': '1'}]
        )
        assert self.nextbus.is_valid_direction('north', '1')

    def test_is_valid_direction_not_direction(self):
        assert not self.nextbus.is_valid_direction('lol', '1')

    def test_is_valid_direction_not_for_route(self):
        self.nextbus.get_route_directions = MagicMock(
            return_value=[{'Value': '4'}, {'Value': '1'}]
        )
        assert not self.nextbus.is_valid_direction('east', '1')

    # get_time_remaining test

    def test_get_time_remaining_no_data(self):
        self.nextbus.get_time_point_departures = MagicMock(return_value=[])
        assert datetime.timedelta(-1) == self.nextbus.get_time_remaining(
            'north', 'fake_stop', 'fake_route'
        )

