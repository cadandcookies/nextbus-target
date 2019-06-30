import argparse
import datetime
import json
import logging
import sys
from typing import Dict, List, Union

import requests


class NextBus:
    BASE_URL = "http://svc.metrotransit.org/NexTrip/"
    ALL_ROUTES_URL = BASE_URL + "Routes"
    ROUTES_URL = BASE_URL + "Routes/"
    DIR_URL = BASE_URL + "Directions/"
    STOP_URL = BASE_URL + "Stops/"
    JSON_FORMAT = "?format=json"

    directions = {'south': '1', 'east': '2', 'west': '3', 'north': '4'}
    directions_inverse = {'1': 'south', '2': 'east', '3': 'west', '4': 'north'}

    def __init__(self):
        self.log = self.build_logger()
        self.parser = self.build_parser()
        self.cache = {}

    def run(self, arguments):
        self.log.debug(f"Raw Args: {arguments}")
        parsed_args = self.parser.parse_args(arguments)
        self.log.debug(f"Parsed Args: {parsed_args}")

        routes = self.get_valid_routes_for_name(parsed_args.route)

        if not routes:
            valid_routes = [route.get('Description') for route in self.get_all_routes()]
            self.log.error(
                f"No valid route for {parsed_args.route}. Valid routes are: {valid_routes}"
            )
            return
        if len(routes) > 1:
            self.log.error(
                f"Route {parsed_args.route} was ambiguous, matches: {routes}"
            )
            return

        route = routes[0].get('number')

        if not self.is_valid_direction(parsed_args.direction, route):
            return

        direction = self.directions[parsed_args.direction.lower()]

        stops = self.get_valid_stops_for_route(parsed_args.stop, route, direction)

        if not stops:
            valid_stops = [
                stop.get('Text') for stop in self.get_route_stops(route, direction)
            ]
            self.log.error(
                f"No valid stop for {parsed_args.stop}. Valid stops are: {valid_stops}"
            )
            return
        if len(stops) > 1:
            self.log.error(f"Route {parsed_args.stop} was ambiguous, matches: {stops}")
            return

        stop = stops[0].get('Value')

        time_remaining = self.get_time_remaining(direction, stop, route)
        self.log.debug(f"Time remaining: {time_remaining}")
        if time_remaining.days >= 0:
            print(f"{time_remaining.seconds / 60} minutes")

    def get_time_remaining(
        self, direction: str, stop: str, route: str
    ) -> datetime.timedelta:
        data = self.get_time_point_departures(direction, stop, route)
        if not data:
            return datetime.timedelta(-1)
        timestring = data[0]['DepartureTime'][6:-10]
        next_bus = datetime.datetime.fromtimestamp(int(timestring))
        now = datetime.datetime.now()
        self.log.debug(
            f"Current time: {now.isoformat()}. Next bus: {next_bus.isoformat()}"
        )
        wait_time = next_bus - now
        self.log.debug(f"Next bus in: {(wait_time)}")
        return wait_time

    def get_valid_routes_for_name(self, route: str) -> List[dict]:
        return [
            {'name': route_desc.get('Description'), 'number': route_desc.get('Route')}
            for route_desc in self.get_all_routes()
            if route.upper() in route_desc.get('Description').upper()
        ]

    def get_valid_stops_for_route(
        self, stop: str, route: str, direction: str
    ) -> List[dict]:
        return [
            stop_desc
            for stop_desc in self.get_route_stops(route, direction)
            if stop.upper() in stop_desc.get('Text').upper()
        ]

    def is_valid_direction(self, direction: str, route: str) -> bool:
        if direction.lower() not in self.directions.keys():
            self.log.error(
                f"{direction} is not a valid direction. Valid directions are: {list(self.directions.keys())}"
            )
            return False
        valid_directions = [
            route_dir.get('Value') for route_dir in self.get_route_directions(route)
        ]
        if self.directions[direction.lower()] not in valid_directions:
            valid_direction_names = [
                self.directions_inverse.get(value) for value in valid_directions
            ]
            self.log.error(
                f"{direction} is not a valid direction. Valid directions for route {route} are: {valid_direction_names}"
            )
            return False
        return True

    def get(self, url: str) -> Union[List, Dict]:
        url = url + self.JSON_FORMAT
        self.log.debug(f"GET {url}")
        try:
            request = None
            request = requests.get(url)
            return request.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError) as err:
            self.log.debug(
                f"Failed to GET {url}: {err} : Request: {request if request else 'None'}"
            )
        return []

    def get_all_routes(self, force_update: bool = False):
        return self.__cache('all_routes', self.ALL_ROUTES_URL, force_update)

    def get_route_directions(
        self, route: str, force_update: bool = False
    ) -> List[dict]:
        return self.__cache(f"dir_{route}", f"{self.DIR_URL}{route}", force_update)

    def get_route_stops(
        self, route: str, direction: str, force_update: bool = False
    ) -> List[dict]:
        return self.__cache(
            f"stops_{route}_{direction}",
            f"{self.STOP_URL}{route}/{direction}",
            force_update,
        )

    def get_time_point_departures(
        self, direction: str, stop: str, route: str, force_update: bool = False
    ) -> List[dict]:
        return self.__cache(
            f"time_point_{route}_{direction}_{stop}",
            f"{self.BASE_URL}{route}/{direction}/{stop}",
            force_update,
        )

    def __cache(self, key: str, url: str, force_update: bool = False):
        if not force_update and self.cache.get(key):
            return self.cache.get(key)
        value = self.get(url)
        if not value:
            self.log.debug(f"Failed to GET from URL")
            return value
        self.cache.update({key: value})
        return value

    def build_parser(self):
        parser = argparse.ArgumentParser(
            description="Identify when the next bus is departing in the specified direction from a specified stop using the NexTrip API"
        )
        parser.add_argument(
            "route",
            type=str,
            help="The route to look for the next bus for. This can be any unambiguous substring of a valid stop.",
        )
        parser.add_argument(
            "stop",
            type=str,
            help="The stop to look for the next bus for. This can be any unambiguous substring of a valid stop.",
        )
        parser.add_argument(
            "direction",
            type=str,
            help="The direction to look for the next bus for. Valid directions are north, south, east, and west.",
        )
        return parser

    def build_logger(self):
        logger = logging.getLogger("nextbusapp")
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('nextbus.log')
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        # add the handlers to the logger
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger


if __name__ == "__main__":
    nextbus = NextBus()
    nextbus.run(sys.argv[1:])
