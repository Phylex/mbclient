mbclient
========
Client software and on the fly visualisation tools for the moessbauer effect.

The client software
-------------------
The client software is a command line tool capable of connecting to the Red-Pitaya running the MBFilter_
program in server mode, providing the server on the Red-Pitaya with all the neccesary information to configure itself properly and to store the data
received from the Red-Pitaya in a `.csv` file for Analysis by the student and also Visualise the data as a pulse-height spektrum and a 2d spektrum of
pulse height vs. Digital Function Generator Address. The Visualisation is updated continuously and can be exited without interfering with the data
taking procedures.

The program structure
---------------------
The mbclient package consists of the cli application located at `cli.py` and associated functions in the `mbclient.py` file. The command line program
operates asynchronously with asyncio_. There are a total of three tasks.
1. The user facing task waits for a `stop` input from the user and sends a terminate signal to the other running tasks.
2. The `process_data` task opens a websocket connection to the Red-Pitaya experiment, reads in the data from there and passes it along to 'consumer'
   tasks.
3. The `write_to_file` task writes the decoded data it receives from the task 2 and writes it into an csv file.
4. The `plot_data` task starts a second process, that is responsible for 'live' plotting of the data and forwards the data to it via a PIPE.

The `mbdatatypes.py` file contains the Class that represents the result coming from the Red-Pitaya. It contains methods to decode the raw data from
the websocket and methods to transform the data read to a csv entry.

The `mbplotter.py` file contains the Class that is spawned off into the second process to plot the data, as well as a class that acts as an API for
sending data to the plotting process via the `plot(data)` funciton. The characteristics and details of the plot are encoded in the `ProcessPlotter` class.


Notes on Matplotlib
-------------------
Matplotlib does quite a lot of things. One of them being the implementation of it's own event loop similar to the one used from asyncio. With the
event loop comes the ability to set a timer that fires a callback function that updates the plot. All this is implemented in the `ProcessPlotter`
class. The Pipe between the processes is used as a data buffer.


.. _MBFilter https://github.com/phylex/MBFilter
.. _asyncio https://docs.python.org/3/library/asyncio.html
