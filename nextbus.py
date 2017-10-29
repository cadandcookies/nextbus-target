import json
import logging
import urllib.request
import sys
import pathlib
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
LOG_CONSOLE_LEVEL = logging.DEBUG

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
    urlin = urlin + JSON_FORMAT
    LOG.debug("Requested URL: " + urlin)
    with urllib.request.urlopen(urlin) as url:
        data = json.loads(url.read().decode())
    LOG.info("Data obtained from URL: " + urlin)
    LOG.debug(data)
    return data

def getJSONFromFile(fname):
    with open(fname, 'r') as f:
        data = json.load(f)
    LOG.info("Data obtained from File: " + fname)
    LOG.debug(data)
    return data

def isFileCreated(filename):
    file = pathlib.Path(filename)
    if file.is_file():
        LOG.debug("File " + filename + " already exists")
        return True
    LOG.debug("File " + filename + " doesn't already exist")
    return False

## Data Access Methods
def getDirections(route):
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
    if not isValidStop(route, direction, stop):
        return None
    return getJSONFromURL(DEP_URL + str(route) + "/" + str(direction.value) + "/" + stop)

## Data Test Methods
def isValidRoute(route):
    routes = getJSONFromFile(DATA_DIR + ROUTES_FILE)
    for troute in routes:
        if int(troute['Route']) == route:
            LOG.debug("Route " + str(route) + " is a valid route.")
            return True
    LOG.debug("Route " + str(route) + " is not a valid route.")
    return False

def isValidDirection(route, direction):
    if not isValidRoute(route):
        return False
    directions = getDirections(route)
    for dir in directions:
        if int(dir["Value"]) == direction.value:
            LOG.debug("Route " + str(route) + " goes " + direction.name)
            return True
    LOG.debug("Route " + str(route) + " does not go " + direction.name)
    return False

def isValidStop(route, direction, stop):
    if not isValidDirection(route, direction):
        return False
    stops = getStops(route, direction)
    for busstop in stops:
        if busstop['Value'] == stop:
            LOG.debug("Stop " + stop + " is on Route " + str(route) + " going " + direction.name)
            return True
    LOG.debug("Stop " + stop + " is not on Route " + str(route) + " going " + direction.name)
    return False

## Search Methods

def matchToRoute(routename):
    routefilename = DATA_DIR + ROUTES_FILE
    data = getJSONFromFile(routefilename)
    for route in data:
        if routename in route["Description"]:
            LOG.debug("Matched route substring \"" + routename + "\" to " + route["Description"] + ", route number " + route["Route"] )
            return int(route["Route"])
    LOG.error("Could not match route substring " + routename)
    return -1

def matchToDirection(directionname):
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
    stopdata = getStops(route, direction)
    for stop in stopdata:
        if stationname in stop["Text"]:
            LOG.debug("Matched stop substring \"" + stationname + "\" to " + stop["Text"] + ", station code " + stop["Value"])
            return stop["Value"]
    LOG.error("Could not match stop substring " + stationname)
    return None

# Main
def main():
    LOG.debug("Route Input: " + sys.argv[1])
    LOG.debug("Stop Input: " + sys.argv[2])
    LOG.debug("Direction Input: " + sys.argv[3])

    route = matchToRoute(sys.argv[1])
    direction = matchToDirection(sys.argv[3])
    stop = matchToStop(route, direction, sys.argv[2])

    LOG.debug("Parsed: ")
    LOG.debug("Route: " + str(route))
    LOG.debug("Stop: " + stop)
    LOG.debug("Direction: " + direction.name)

    getTimePointDepartures(route, direction, stop)

main()