import argparse as ap
import asyncio
import time
import numpy as np
import websockets
import yaml
import sys
import mbclient.mbdatatypes as mbd
from mbclient.mbplotter import NBPlot


def parse_config_from_yml(path_to_yaml):
    with open(path_to_yaml, 'r') as f:
        config = yaml.safe_load(f.read())
    try:
        k = config['basic']['rise-time']
        l = config['basic']['hold-time']
        m = config['basic']['pulse-decay-time']
        pthresh = config['basic']['pulse-height-threshhold']
        ip = config['environment']['server-ip']
        port = config['environment']['server-port']
    except KeyError as e:
        print(f'The setting {e} was not found in the config file {path_to_yaml} it is however neccesary')
        sys.exit(1)
    if 'advanced' in config.keys():
        if 'accumulation-time' in config['advanced'].keys():
            accum_time = config['advanced']['accumulation-time']
        else:
            accum_time = int(0.1 * k)+l
        if 'debug' in config['advanced'].keys():
            debug = config['advanced']['debug']
        else:
            debug = False
    else:
        accum_time = int(0.1 * k)+l
        debug = False
    return (k, l, m, pthresh, accum_time, ip, port, debug)



async def process_data(uri, out_queues, debug):
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
            if not plotter.joined:
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


async def amain(uri, histmin, histmax, plot, output, debug):
    print('To stop the data taking, please type "stop" during execution')
    if plot:
        plotter = NBPlot(histmin, histmax)
        await asyncio.sleep(5)
    queues = []
    file_aqueue = asyncio.Queue()
    queues.append(file_aqueue)
    if plot:
        plot_aqueue = asyncio.Queue()
        queues.append(plot_aqueue)
    asyncio.create_task(write_to_file(output, file_aqueue))
    if plot:
        asyncio.create_task(plot_data(plot_aqueue, plotter))
    asyncio.create_task(process_data(uri, queues, debug))
    result = ''
    while result not in ['stop', 'quit']:
        result = await read_stdin()
    print('')
    return True

