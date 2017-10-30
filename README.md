# nextbus-target

nextbus-target is a tool for finding out how long it will take for the next bus to arrive given a specific route, stop, and direction in the Minneapolis-St. Paul metro area transit system.

It was complete by Nick Aarestad as a coding assignment for Target.

## Requirements

nextbus-target is written in Python 3, and requires that Python 3 is installed. The program was tested on Python 3.6.3 and is not guaranteed to work on earlier versions of Python.

## Using
The program is designed to take three arguments-- a string that is part of a route's description, a string that is part of a station on that route's name, and a direction. If these arguments are not present or valid, it politely lets the user know. If the string matches multiple stops or routes, there is no guarantee as to which stop or route it will test.

An example use may be:

    py nextbus.py "Blue" "Cedar" "North"

Which would return the time in minutes until the next Blue Line train going North arrived at Cedar-Riverside Station.

## Testing
While no explicit tests were written for this program, it would be relatively easy to create some and test on any machine with a Python 3 installation and an internet connection. Both positive and negative hand testing was done for the Blue Line, Green Line, and Route 3 with a variety of inputs.


