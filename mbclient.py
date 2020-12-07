#!/usr/bin/python

# WS client example

import asyncio
import functools
import sys
import argparse as ap
import websockets
import numpy as np
import matplotlib.pyplot as plt
import mbdatatypes as mbd

class Prompt:
    """Class that encapsulates the stdin in an asynchronous fashion so
    it can be used to stop the data-taking.
    """
    def __init__(self, loop=None):
        """initialize the object and add a reader to the event-loop"""
        self.loop = loop or asyncio.get_event_loop()
        self.queue = asyncio.Queue()
        self.loop.add_reader(sys.stdin, self.got_input)

    def got_input(self):
        """put a task onto the queue that reacts to a std readline"""
        asyncio.ensure_future(self.queue.put(sys.stdin.readline()), loop=self.loop)

    async def __call__(self, msg, end='\n', flush=False):
        """this function executes when the object gets called, it's the
        part that initiates the whole thing"""
        print(msg, end=end, flush=flush)
        return (await self.queue.get()).rstrip('\n')

async def process_data(uri, output, stop_event, process_tasks, max_count):
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
        output.write("timestamp,peak_height,cycle,speed\n")
        count = 0
        while True:
            if stop_event.is_set():
                await websocket.close()
                break
            line = await websocket.recv()
            peak = mbd.MeasuredPeak.decode_from_line(line)
            output.write(peak.as_line())
            count += 1
            print("measured peaks: {}".format(count), end='\r')
            for task in process_tasks:
                asyncio.create_task(task(peak))
            if max_count is not None:
                if  max_count <= count:
                    break

async def read_from_keyboard(raw_input, stopEvent):
    while True:
        command = await raw_input("enter 'stop' to stop the data-taking:\n")
        if command.strip() in ['exit', 'quit', 'Quit', 'stop']:
            stopEvent.set()
            break

async def main():
    parser = ap.ArgumentParser(description='Client application for the Moessbauereffect\
            experiment, connects to the server and stores the Data on the local machine')
    parser.add_argument('K', help='The parameter of the\
            filter that sets the steepness of the flank of the trapezoid', type=int)
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

    stopEvent = asyncio.Event()
    args = parser.parse_args()

    # this is a stdin replacement that is async
    prompt = Prompt()
    raw_input = functools.partial(prompt, end='', flush=True)

    uri = f'ws://{args.IP}:{args.Port}/websocket\
?k={args.K}&l={args.L}&m={args.M}&pthresh={args.peakthresh}&t_dead={args.deadtime}'

    output = open(args.output, 'w+')
    await asyncio.gather(
            process_data(uri, output, stopEvent, [], args.count),
            read_from_keyboard(raw_input, stopEvent),
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
