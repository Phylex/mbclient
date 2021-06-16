#!/usr/bin/python3

import argparse as ap
import asyncio
import time
import numpy as np
import websockets
import mbdatatypes as mbd
from mbplotter import NBPlot

async def process_data(uri, out_queues):
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
            except (asyncio.CancelledError,
                    websockets.exceptions.ConnectionClosedError):
                print(' '*40, end='\r')
                print('closing websocket')
                print('A total of {} peaks where recorded'.format(count))
                for queue in out_queues:
                    queue.put_nowait(None)
                return True
            if not debug:
                if len(msg) % 12 != 0:
                    raise ValueError("msg wrong length: {}".format(len(msg)))
                peaks = len(msg)/12
                decoded_peaks = []
                for i in range(int(peaks)):
                    pd = msg[i*12:(i+1)*12]
                    decoded_peaks.append(mbd.MeasuredPeak.decode_from_bytes(pd))
                    count += 1
                for peak in decoded_peaks:
                    for queue in out_queues:
                        queue.put_nowait(peak)
                print("measured peaks: {}".format(count), end='\r')
            else:  # this is the debug part
                peak = mbd.MeasuredPeak.decode_from_line(msg)
                count += 1
                print("measured peaks: {}".format(count), end='\r')
                for queue in out_queues:
                    queue.put_nowait(peak)


async def plot_data(queue, plotter):
    data_to_send = []
    while True:
        try:
            data = await queue.get()
        except asyncio.CancelledError:
            plotter.plot(None)
            print('Shutting down plotter (this may take a few seconds)...')
            return True
        if data is None:
            plotter.plot(None)
            return True
        if len(data_to_send) < 1000:
            data_to_send.append(data)
        else:
            data_to_send.append(data)
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
    result = await loop.run_in_executor(None, input)
    return result


async def main(uri, args):
    print('To stop the data taking, please type "stop" during execution')
    if args.plot:
        plotter = NBPlot(args.histmin, args.histmax)
        await asyncio.sleep(5)
    queues = []
    file_aqueue = asyncio.Queue()
    queues.append(file_aqueue)
    if args.plot:
        plot_aqueue = asyncio.Queue()
        queues.append(plot_aqueue)
    asyncio.create_task(write_to_file(args.output, file_aqueue))
    if args.plot:
        asyncio.create_task(plot_data(plot_aqueue, plotter))
    asyncio.create_task(process_data(uri, queues))
    result = ''
    while result not in ['stop', 'quit']:
        result = await read_stdin()
    print('')
    return True


if __name__ == '__main__':
    parser = ap.ArgumentParser(description='Client application for\
            the Moessbauereffect experiment, connects to the server\
            and stores the Data on the local machine')
    parser.add_argument('K', help='Filter parameter that determins\
            the steepness pf the trapezoid', type=int)
    parser.add_argument('L', help='The parameter of the\
            signal filter that determins the duration of the plateau\
            of the trapezoid', type=int)
    parser.add_argument('M', help='The multiplication factor\
            that determins the decay time of the pulse that\
            the filter responds best to', type=int)
    parser.add_argument('peakthresh', help='The minimum hight of a detected\
            peak as not to be considered noise', type=int)
    parser.add_argument('accumtime', help='The time the filter accumulates\
            events for to pick the highest signal as "detected Peak",\
            sets the maximum frequency of events that the filter can\
            effectively distinguish', type=int)
    parser.add_argument('IP', help='IP address of the red-pitaya\
            that is connected to the experiment', type=str)
    parser.add_argument('output', help='File to write the data to. The output\
            is a CSV file with one line per event')
    parser.add_argument('-p', '--Port', help='Port of the TCP connection.\
            defaults to 8080', default=8080, type=int)
    parser.add_argument('-hmax', '--histmax', help='maximum pulse height of the\
            pulse height spectrum', type=int, default=18000000)
    parser.add_argument('-hmin', '--histmin', help='minimum pulse height of the\
            pulse height spectrum', type=int, default=500000)
    parser.add_argument('-plt' '--plot', action='store_true', help='enable plotting')

    args = parser.parse_args()

    debug = False
    if not debug:
        URI = f'ws://{args.IP}:{args.Port}/websocket\
?k={args.K}&l={args.L}&m={args.M}&pthresh={args.peakthresh}\
&t_dead={args.accumtime}'
    else:
        URI = 'ws://localhost:8080'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(URI, args))
    pending = asyncio.all_tasks(loop=loop)
    for task in pending:
        task.cancel()
    group = asyncio.gather(*pending, return_exceptions=True)
    loop.run_until_complete(group)
    loop.stop()
    loop.close()
