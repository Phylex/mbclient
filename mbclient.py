#!/usr/bin/python3

# WS client example

import asyncio
from aiofile import AIOFile
import functools
import sys
import argparse as ap
import websockets
import time
import numpy as np
import matplotlib.pyplot as plt
import mbdatatypes as mbd
import multiprocessing as mp

class ProcessPlotter:
    def __init__(self):
        self.data = []
        self.patches = None
        self.hist = None

    def terminate(self):
        plt.close('all')

    def call_back(self):
        while self.pipe.poll():
            command = self.pipe.recv()
            if command is None:
                self.terminate()
                return False
            else:
                h, _ = np.histogram(command, self.bins)
                self.hist_values += h
                for c, r in zip(self.hist_values, self.patches.patches):
                    r.set_height(c)
        self.fig.canvas.draw()
        return True

    def __call__(self, pipe, bins):
        print('starting plotter...')
        self.pipe = pipe
        self.bins = bins
        self.hist_values = np.zeros_like(bins[1:])
        self.fig, self.ax = plt.subplots()
        self.hist, self.bins, self.patches = self.ax.hist([], self.bins,
                color = 'blue')
        self.ax.set_ylim(0, 5000)
        self.ax.set_xlabel(r'Pulshoehe $\propto$ Energie')
        self.ax.set_ylabel('Ereignisanzahl')
        self.ax.grid()
        self.ax.set_title('Pulshoehenspektrum')
        timer = self.fig.canvas.new_timer(interval=500)
        timer.add_callback(self.call_back)
        timer.start()
        plt.show()

class NBPlot:
    def __init__(self, bins):
        self.plot_pipe, plotter_pipe = mp.Pipe()
        self.plotter = ProcessPlotter()
        self.plot_process = mp.Process(target=self.plotter, args=(plotter_pipe, bins), daemon=True)
        self.plot_process.start()
    def plot(self, data=None, finished=False):
        send = self.plot_pipe.send
        if finished:
            send(None)
        else:
            if data is None:
                data = np.random.rand(100)
            send(data)


async def process_data(uri, file_aqueue, plot_aqueue):
    """Coroutine that receives the data from the server

    This coroutine is the only one that directly reads frames from
    the websocket. The more expensive task of processing the frame
    is delegated to other tasks that are spun up from here but not
    waited upon

    Args:
        uri (str): The uri of the websocket of the redPitaya.
        output (file): The location to write the processed output to.
            this either a file or stdout
        stop_event (asyncio.Event): The tasks checks this event to
            figure out if the user has terminated the program via
            a 'stop' on the commandline
        process_tasks (list of callables): A list of callable objects
        that will be called on receiving a frame with the frame as
        argument
    """
    async with websockets.connect(uri) as websocket:
        print("connected to websocket")
        count = 0
        while True:
            try:
                msg = await websocket.recv()
            except (asyncio.CancelledError, websockets.exceptions.ConnectionClosedError) as e:
                if e is asyncio.CancelledError:
                    await websocket.close()
                plot_aqueue.put_nowait(None)
                file_aqueue.put_nowait(None)
                print('', end='\r')
                print('Shutting Down')
                print('Parameters of the experiment:')
                print('k: {}\nl: {}\nm: {}'.format(args.K, args.L, args.M))
                print('peak threshhold: {}'.format(args.peakthresh))
                print('accumulation time: {}'.format(args.deadtime))
                print('')
                print('A total of {} peaks where recorded'.format(count))
                return True
            if not args.debug:
                if len(msg) % 12 != 0:
                    raise ValueError("msg wrong length: {}".format(len(msg)))
                peaks = len(msg)/12
                decoded_peaks = []
                for i in range(int(peaks)):
                    pd = msg[i*12:(i+1)*12]
                    decoded_peaks.append(mbd.MeasuredPeak.decode_from_bytes(pd))
                    count += 1
                    print("measured peaks: {}".format(count), end='\r')
                file_aqueue.put_nowait(decoded_peaks)
                plot_aqueue.put_nowait(decoded_peaks)
            else:
                if msg is None:
                    websocket.close()
                    plot_aqueue.put_nowait(None)
                    file_aqueue.put_nowait(None)
                    print('', end='\r')
                    print('Shutting Down')
                    print('Parameters of the experiment:')
                    print('k: {}\nl: {}\nm: {}'.format(args.k, args.l, args.m))
                    print('peak threshhold: {}'.format(args.peakthresh))
                    print('accumulation time: {}'.format(args.deadtime))
                    print('')
                    print('A total of {} peaks where recorded'.format(count))
                    return True
                peak = mbd.MeasuredPeak.decode_from_line(msg)
                count += 1
                print("measured peaks: {}".format(count), end='\r')
                await file_aqueue.put(peak)
                await plot_aqueue.put(peak)


async def plot_data(queue, plotter):
    data_to_send = []
    while True:
        try:
            data = await queue.get()
        except asyncio.CancelledError:
            plotter.plot(None)
            print('Shutting down plotter ...')
            time.sleep(3)
            return True
        if data is None:
            plotter.plot(None)
            return True
        if len(data_to_send) < 1000:
            data_to_send.append(data.peak_height)
        else:
            data_to_send.append(data.peak_height)
            plotter.plot(data_to_send)
            data_to_send = []
        queue.task_done()


async def write_to_file(filename, queue):
   with open(filename, 'w+') as f:
        f.write("timestamp,peak_height,cycle,speed\n")
        while True:
            try:
                peak = await queue.get()
                if peak is None:
                    f.close()
                    queue.task_done()
                    return True
                f.write(peak.as_line())
                queue.task_done()
            except asyncio.CancelledError:
                f.close()
                return True


async def read_stdin() -> str:
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, sys.stdin.readline)


if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Client application for the Moessbauereffect\
            experiment, connects to the server and stores the Data on the local machine')
    parser.add_argument('-d', '--debug', help='configures the uri for debug, overrides the IP parameter', action='store_true')
    parser.add_argument('K', help='Filter parameter that determins the steepness pf the trapezoid', type=int)
    parser.add_argument('L', help='The parameter of the\
            signal filter that determins the duration of the plateau of the trapezoid', type=int)
    parser.add_argument('M', help='The multiplication factor\
            that determins the decay time of the pulse that the filter responds best to', type=int)
    parser.add_argument('peakthresh', help='The minimum hight of a detected\
            peak as not to be considered noise', type=int)
    parser.add_argument('deadtime', help='The time the filter accumulates events\
            for to pick the highest signal as "detected Peak", sets the maximum frequency of\
            events that the filter can effectively distinguish', type=int)
    parser.add_argument('IP', help='IP address of the red-pitaya\
            that is connected to the experiment', type=str)
    parser.add_argument('output', help='File to write the data to. If this is not set\
            the program writes to stdout')
    parser.add_argument('-p', '--Port', help='Port of the TCP connection. defaults to 8080',
            default=8080, type=int)
    parser.add_argument('-c', '--count', help='Sets the number of events to collect and process\
            before stopping automatically')

    args = parser.parse_args()

    if not args.debug:
        uri = f'ws://{args.IP}:{args.Port}/websocket\
?k={args.K}&l={args.L}&m={args.M}&pthresh={args.peakthresh}&t_dead={args.deadtime}'
    else:
        uri = 'ws://localhost:8080'

    HIST_BINS = np.linspace(0, 15000000, 3000)
    plotter = NBPlot(HIST_BINS)
    time.sleep(5)
    file_aqueue = asyncio.Queue()
    plot_aqueue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    t1 = loop.create_task(write_to_file(args.output, file_aqueue))
    t2 = loop.create_task(plot_data(plot_aqueue, plotter))
    t3 = loop.create_task(process_data(uri, file_aqueue, plot_aqueue))
    group = asyncio.gather(t1, t2, t3, return_exceptions=True)
    loop.run_until_complete(group)
    print('run process_data to completion')
    loop.close()
