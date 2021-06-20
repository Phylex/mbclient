# mbclient
Client software and on the fly visualisation tools for the moessbauer effect.

## The client software
The client software is a command line tool capable of connecting to the Red-Pitaya running the [MBFilter](https://github.com/phylex/MBFilter)
program in server mode, providing the server on the Red-Pitaya with all the neccesary information to configure itself properly and to store the data
received from the Red-Pitaya in a `.csv` file for Analysis by the student and also Visualise the data as a pulse-height spektrum and a 2d spektrum of
pulse height vs. Digital Function Generator Address. The Visualisation is updated continuously and can be exited without interfering with the data
taking procedures.

## Configuration options
The client software can be configured in two ways, the main method of configuration is a yaml config file. An example is provided in this repository
and printed here for convenience:
```
basic:
  rise-time: 10
  hold-time: 20
  pulse-decay-time: 390
  pulse-height-threshhold: 1000000

environment:
  server-ip: '192.168.0.2'
  server-port: '8080'
```

There is an advanced option available to override the internally calculated accumulation-time. To set this add the following section to the
config file:
```
advanced:
  accumulation-time: 22
```

The configuration options `rise-time`, `hold-time` and `pulse-decay-time` are the parameters of the trapezoidal filter. The `pulse-height-threshhold`
is used to suppress small (and thus low energy) peaks and primarily acts to reduce noise, as the high frequency of the noise can overwhelm the filter.
The IP of server should not change through the course of a semester and the port only changes if explicitly set at server startup.
The accumulation-time is used to avoid counting one peak multiple times. It should only be set if there are major problems with the setup, as it is
automatically calculated from the `rise-time` and `hold-time` of the trapezoidal filter.

The second way is via command line arguments, that are similarly named to the configuration options. The command line values, when given, override the
configuration options specified in the config file.

### Configuring plotting
The command line also has a flag to disable plotting. Disabling plotting should be done when attempting the long duration measurements as plotting the
values slows down the process significantly after a while. The plot can be closed at any time during the program execution without interrupting the
data taking activities. It however cannot be restarted after being closed.

The `--histmin` and `--histmax` options set the lower and upper bound on the pulse-height of the events being plotted. The bin width is adjusted
automatically. The plot also automatically rescales so that all the data is visible.

## Behaviour of the Program
The server will stop sending events, if the FPGA-Internal hardware buffer overflows. This is an indicator, that the system as a whole is overwhelmed
with the number of events. As the buffer is only so large, the overflowing is poisson distributed. The larger the average event rate, the more likely
it is for the buffer to overflow due to many events in short succession. If this happens within the first 5 minutes of the experiment, try increasing
the `pulse-height-threshhold` about 50000, this cuts more of the signal that is suspected to be noise and reduces the likelihood of the filter
overflowing and the experiment being halted.

To restart the experiment, simply call `mb-client` again. The Red-pitaya will automatically reconfigure and start the next measurement.

In the (very rare) case where this does not happen, go to the ssh connection to the Red-pitaya and quit the server with `<Ctrl>C` then call the
`./start_server.sh` again.

## The program structure
The mbclient package consists of the cli application located at `cli.py` and associated functions in the `mbclient.py` file. The command line program
operates asynchronously with [asyncio](https://docs.python.org/3/library/asyncio.html). There are a total of three tasks.
1. The user facing task waits for a `stop` input from the user and sends a terminate signal to the other running tasks.
2. The `process_data` task opens a websocket connection to the Red-Pitaya experiment, reads in the data from there and passes it along to 'consumer'
   tasks.
3. The `write_to_file` task writes the decoded data it receives from the task 2 and writes it into an csv file.
4. The `plot_data` task starts a second process, that is responsible for 'live' plotting of the data and forwards the data to it via a PIPE.

The `mbdatatypes.py` file contains the Class that represents the result coming from the Red-Pitaya. It contains methods to decode the raw data from
the websocket and methods to transform the data read to a csv entry.

The `mbplotter.py` file contains the Class that is spawned off into the second process to plot the data, as well as a class that acts as an API for
sending data to the plotting process via the `plot(data)` funciton. The characteristics and details of the plot are encoded in the `ProcessPlotter` class.

## Notes on Matplotlib
Matplotlib does quite a lot of things. One of them being the implementation of it's own event loop similar to the one used from asyncio. With the
event loop comes the ability to set a timer that fires a callback function that updates the plot. All this is implemented in the `ProcessPlotter`
class. The Pipe between the processes is used as a data buffer.

