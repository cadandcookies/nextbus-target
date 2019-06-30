# nextbus-target

nextbus-target is a tool for finding out how long it will take for the next bus to arrive given a specific route, stop, and direction in the Minneapolis-St. Paul metro area transit system.

It was completed by Nick Aarestad as a coding assignment for Target.

## Requirements

nextbus-target is written in Python 3, and requires that Python 3 is installed. The program was tested on Python 3.7.1 and is not guaranteed to work on earlier versions of Python. It is recommended that the user create a virtual environment to run this application in.

You can `pip3 install -r requirements.txt` to install the packages necessary for running and testing this application.

## Using
The program is designed to take three arguments-- a string that is part of a route's description, a string that is part of a station on that route's name, and a direction. If these arguments are not present or valid, it politely lets the user know. If the string matches multiple stops or routes, there is no guarantee as to which stop or route it will test.

An example use may be:

`python3 nextbus.py "Blue" "Cedar" "north"`

Which would return the time in minutes until the next Blue Line train going North arrived at Cedar-Riverside Station.

You can use `python3 nextbus.py -h` to view the help for this app. It will also do its best to let you know what arguments may be valid if you supply it with arguments it can't interpret.

## Testing
This application has comprehensive suite of functional and unit tests. These tests may be run by running `make test` in the root directory, which will automatically install dependencies, assuming it has access to a valid `python3` on the path.


