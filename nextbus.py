import json
import logging
import urllib.request
import sys
import pathlib
import datetime
from enum import Enum

# Constants
## URLs
BASE_URL = "http://svc.metrotransit.org/NexTrip/"
DIR_URL = BASE_URL + "Directions/"
STOP_URL = BASE_URL + "Stops/"
DEP_URL = BASE_URL
JSON_FORMAT = "?format=json"

## Files
DATA_DIR = "data/"
ROUTES_FILE = "routes.json"

## Directions
class Direction(Enum):
    SOUTHBOUND = 1
    EASTBOUND = 2
    WESTBOUND = 3
    NORTHBOUND = 4

# Logger
LOG_FILE_LEVEL = logging.DEBUG
LOG_CONSOLE_LEVEL = logging.ERROR

def loggingSetup():
    sublogger = logging.getLogger("nextbusapp")
    sublogger.setLevel(logging.DEBUG)
    fh = logging.FileHandler('nextbus.log')
    fh.setLevel(LOG_FILE_LEVEL)
    ch = logging.StreamHandler()
    ch.setLevel(LOG_CONSOLE_LEVEL)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    sublogger.addHandler(fh)
    sublogger.addHandler(ch)
    return sublogger

LOG = loggingSetup()

# Functions
## JSON and File Operations

def getJSONFromURL(urlin):
    """Gets JSON data from a url

    Gets JSON from a URL, assuming the URL is a valid endpoint of the MetroTransit API
    Automatically handles formatting the request to use JSON, instead of the default XML
    Note: Exceptions from this function ARE NOT currently handled. Pass a valid URL!

    Args:
        urlin: A URL in string form to retrive the JSON data from

    Returns:
        The decoded JSON data
    """
    urlin = urlin + JSON_FORMAT
    LOG.debug("Requested URL: " + urlin)
    with urllib.request.urlopen(urlin) as url:
        data = json.loads(url.read().decode())
    LOG.info("Data obtained from URL: " + urlin)
    LOG.debug(data)
    return data

def getJSONFromFile(fname):
    """Gets JSON data from a file

    Gets JSON data from the file specified. Does not currently do any error checking for
    whether the file name given is actually a file.

    Args:
        fname: The file name in string format to retrieve the data from

    Returns:
        The decoded JSON data
    """
    with open(fname, 'r') as f:
        data = json.load(f)
    LOG.info("Data obtained from File: " + fname)
    LOG.debug(data)
    return data

def isFileCreated(filename):
    """Checks if a file has been created

    Checks the specified file. Fairly insensitive as it uses pathlib

    Args:
        filename: The file name to check the existence of

    Returns:
        True if file exists, false otherwise
    """
    file = pathlib.Path(filename)
    if file.is_file():
        LOG.debug("File " + filename + " already exists")
        return True
    LOG.debug("File " + filename + " doesn't already exist")
    return False

## Data Access Methods
def getDirections(route):
    """Gets the directions for a specified route

    Gets the directions for a specified route, either by requesting it from the API
    or using a cached file. If the route does not have the directions stored, this
    function will cache them so that future requests do not make an API call.

    Args:
        route: The route to get directions for

    Returns:
        The JSON data indicating the directions for the given route
    """
    LOG.debug("Checking directions for route " + str(route))
    fname = DATA_DIR + str(route) + ".json"
    if not isFileCreated(fname):
        file = open(fname, 'w+')
        dataRaw = getJSONFromURL(DIR_URL + str(route))
        json.dump(dataRaw, file)
        return dataRaw
    data = getJSONFromFile(fname)
    return data

def getStops(route, direction):
    """Get the stops for a given route in the given direction

    Gets the stops for a given route in the given direction, either by requesting it from the API
    or using a cached file. If the route does not have the stops for the directions stored, this
    function will cache them so that future requests do not make an API call.\

    Args:
        route: The route to get stops from (integer)
        direction: The direction to get stops from (Direction enum)

    Returns:
        The converted JSON data for the stops on that route in the direction, or None if the params
        were not valid.
    """
    if not isValidDirection(route, direction):
        LOG.error("Route " + str(route) + " does not go " + direction.name)
        return None
    fname = DATA_DIR + str(route) + direction.name + ".json"
    if not isFileCreated(fname):
        file = open(fname, 'w+')
        dataRaw = getJSONFromURL(STOP_URL + str(route) + "/" + str(direction.value))
        json.dump(dataRaw, file)
        return dataRaw
    data = getJSONFromFile(fname)
    return data

def getTimePointDepartures(route, direction, stop):
    """Gets the timepoint departures data

    Gets the timepoint departure data for the given route, direction, and stop.

    Args:
        route: The route  to get the departure data for
        direction: The direction to get the departure data for
        stop: The stop to get the departure data for

    Returns:
        The converted JSON data for the requested departures, or None if the
        provided data was invalid
    """
    if not isValidStop(route, direction, stop):
        return None
    return getJSONFromURL(DEP_URL + str(route) + "/" + str(direction.value) + "/" + stop)

def getTimeRemaining(route, direction, stop):
    """Gets the time remaining until the next bus/train arrives

    Gets the time remaining until the next bus/train arrives for the given route, direction,
    and stop.

    Args:
        route: The route to get the next bus/train for
        direction: The direction to get the next bus/train for
        stop: The stop to get the next bus/train for

    Returns:
        The time in minutes until the next bus or train arrives
    """
    data = getTimePointDepartures(route, direction, stop)
    timestring = data[0]['DepartureTime'][6:-10]
    LOG.debug(timestring)
    time = datetime.datetime.fromtimestamp(int(timestring))
    curtime = datetime.datetime.now()
    readabletime = time.strftime('%Y-%m-%d %H:%M:%S')
    readablecurtime = curtime.strftime('%Y-%m-%d %H:%M:%S')
    timedif = time - curtime
    timeremaining = divmod(timedif.days * 86400 + timedif.seconds, 60)

    LOG.debug("Current time is: " + readablecurtime)
    LOG.debug("Next bus arrives at: "+ readabletime)
    LOG.debug("Time difference is " + str(timeremaining[0]) + " minutes, " + str(timeremaining[1]) + " seconds.")
    LOG.debug("Next bus in " + str(timeremaining[0]) + " minutes.")
    return timeremaining[0]


## Data Test Methods
def isValidRoute(route):
    """Tests if the given route is valid

    Args:
        route: The route to test

    Returns:
        True if the route exists, false otherwise
    """
    routes = getJSONFromFile(DATA_DIR + ROUTES_FILE)
    for troute in routes:
        if int(troute['Route']) == route:
            LOG.debug("Route " + str(route) + " is a valid route.")
            return True
    LOG.error("Route " + str(route) + " is not a valid route.")
    return False

def isValidDirection(route, direction):
    """Tests if the given direction is valid for the given route

    Args:
        route: The route to test
        direction: The direction to test

    Returns:
        True if the direction is valid, false otherwise
    """
    if not isValidRoute(route):
        return False
    directions = getDirections(route)
    for dir in directions:
        if int(dir["Value"]) == direction.value:
            LOG.debug("Route " + str(route) + " goes " + direction.name)
            return True
    LOG.error("Route " + str(route) + " does not go " + direction.name)
    return False

def isValidStop(route, direction, stop):
    """Tests if a stop is valid for the given route and direction

    Args:
        route: The route to test
        direction: The direction to test
        stop: The stop to test

    Returns:
        True if the stop is valid, false otherwise
    """
    if not isValidDirection(route, direction):
        return False
    stops = getStops(route, direction)
    for busstop in stops:
        if busstop['Value'] == stop:
            LOG.debug("Stop " + stop + " is on Route " + str(route) + " going " + direction.name)
            return True
    LOG.error("Stop " + stop + " is not on Route " + str(route) + " going " + direction.name)
    return False

## Search Methods

def matchToRoute(routename):
    """Checks if the given routename is part of any known routes

    Searches the list of routes to find if the given string is a substring of any known routes

    Args:
        routename: The string to find a match for

    Returns:
        The number of the route the string matches to, or None if no route is found
    """
    routefilename = DATA_DIR + ROUTES_FILE
    data = getJSONFromFile(routefilename)
    for route in data:
        if routename in route["Description"]:
            LOG.debug("Matched route substring \"" + routename + "\" to " + route["Description"] + ", route number " + route["Route"] )
            return int(route["Route"])
    LOG.error("Could not find a route matching " + routename)
    return None

def matchToDirection(directionname):
    """Matches the given direction to a known direction

    Args:
        directionname: The string to find a matching direction for

    Returns:
        The direction enum for the given string, or None if no direction matches
    """
    newdirectionname = directionname.upper() + "BOUND"
    try:
        dir = Direction[newdirectionname]
        LOG.debug("Matched " + directionname + " to " + newdirectionname)
        return dir
    except KeyError:
        LOG.error(directionname + " is not a valid direction. Valid directions are North, South, East, and West.")
        pass
    return None

def matchToStop(route, direction, stationname):
    """Matches a string to known stops for a given route and direction

    Args:
        route: The route to search for a matching stop
        direction: The direction to search for a matching stop
        stationname: The string to search for a matching stop

    Returns:
        The stop code, or None if no stop matches on the given route
    """
    stopdata = getStops(route, direction)
    for stop in stopdata:
        if stationname in stop["Text"]:
            LOG.debug("Matched stop substring \"" + stationname + "\" to " + stop["Text"] + ", station code " + stop["Value"])
            return stop["Value"]
    LOG.error("Could not find a matching stop for " + stationname + " on Route " + str(route))
    return None

# Main
def main():
    LOG.debug("Route Input: " + sys.argv[1])
    LOG.debug("Stop Input: " + sys.argv[2])
    LOG.debug("Direction Input: " + sys.argv[3])

    route = matchToRoute(sys.argv[1])
    if route is None or not isValidRoute(route):
        return
    direction = matchToDirection(sys.argv[3])
    if direction is None or not isValidDirection(route, direction):
        return
    stop = matchToStop(route, direction, sys.argv[2])
    if stop is None or not isValidStop(route, direction, stop):
        return

    LOG.debug("Parsed: ")
    LOG.debug("Route: " + str(route))
    LOG.debug("Stop: " + stop)
    LOG.debug("Direction: " + direction.name)

    time_remaining = getTimeRemaining(route, direction, stop)

    print(str(time_remaining) + " minutes")



main()