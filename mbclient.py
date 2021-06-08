#!/usr/bin/python3

# WS client example

import asyncio
import functools
import sys
import argparse as ap
import websockets
import numpy as np
import matplotlib.pyplot as plt
import mbdatatypes as mb
from multiprocessing import Process, Queue

async def plotting_process(queue, hist_bins, attribute):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    hist, b, patches = plt.hist([], hist_bins)
    while True:
        if queue.empty():
            continue
        peaks = queue.get()
        if type(peaks) == str:
            if peaks == 'stop':
                break
        else:
            data = [peak[attribute] for peak in peaks]
            n, _ = np.histogram(data, hist_bins)
            hist += n
            for c, r in zip(hist, patches.patches):
                r.set_height(c)
            fig.canvas.daw()
            plt.pause(.1)



async def write_to_file(queue, filename):
    with open(filename, 'w+') as f:
        while True
            try:
                peak = await queue.get()
            except asyncio.CancelledError:
                break
            f.write(peak.as_line())

async def write_to_other_process(aqueue, pqueue):
    while True
        try:
            peaks = await aqueue.get()
        except asyncio.CancelledError:
            pqueue.put("stop")
            break
        pqueue.put(peaks)

async def process_data(uri, data_queues):
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
            try:
                msg = await websocket.recv()
            except asyncio.CancelledError:
                await websocket.close()
                print('', end='\r')
                print('Shutting Down')
                print('Parameters of the experiment:')
                print('k: {}\nl: {}\nm: {}'.format(args.k, args.l, args.m))
                print('peak threshhold: {}'.format(args.peakthresh))
                print('accumulation time: {}'.format(args.deadtime))
                print('')
                print('A total of {} peaks where recorded'.format(count))
                break
            if len(msg) % 12 != 0:
                raise ValueError("msg wrong length: {}".format(len(msg)))
            else:
                peaks = len(msg)/12
                decoded_peaks = []
                for i in range(int(peaks)):
                    pd = msg[i*12:(i+1)*12]
                    decoded_peaks.append(mbd.MeasuredPeak.decode_from_bytes(pd))
                    count += 1
                    print("measured peaks: {}".format(count), end='\r')
                for queue in data_queues:
                    await queue.put(decoded_peaks)



async def read_stdin() -> str:
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, sys.stdin.readline)

if __name__ == '__main__':
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

    args = parser.parse_args()

    uri = f'ws://{args.IP}:{args.Port}/websocket\
?k={args.K}&l={args.L}&m={args.M}&pthresh={args.peakthresh}&t_dead={args.deadtime}'

    plt_process_queue = Queue()
    plot_process = Process(target=plotting_process, args=plt_process_queue,))
    plot_process.start()
    plt_aqueue = asyncio.Queue()
    file_aqueue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    loop.create_task(write_to_file(args.output, file_aqueue))
    loop.create_task(write_to_other_process(plt_aqueue, plt_process_queue))
    loop.create_task(process_data(uri, [file_aqueue, plt_aqueue]))
    while True:
        line = loop.run_until_complete(read_stdin())
        if line.strip() in ['exit', 'quit', 'stop', 'Quit']:
            break
    pending = asyncio.all_tasks(loop=loop)
    for task in pending:
        task.cancel()
    group = asyncio.gather(*pending, return_exceptions=True)
    loop.run_until_complete(group)
    loop.close()
    plt_process.join()
