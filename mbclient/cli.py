from mbclient import mbclient
import argparse as ap
import asyncio
import sys


def main():
    parser = ap.ArgumentParser(description='Client application for\
            the Moessbauereffect experiment, connects to the server\
            and stores the Data on the local machine')
    parser.add_argument('-k', '--rise-time', help='Filter parameter that determins\
            the steepness pf the trapezoid', type=int, default=-1)
    parser.add_argument('-l', '--hold-time', help='The parameter of the\
            signal filter that determines the duration of the plateau\
            of the trapezoid', type=int, default=-1)
    parser.add_argument('-m', '--pulse-decay-time', help='The multiplication factor\
            that determines the decay time of the pulse that\
            the filter responds best to', type=int, default=-1)
    parser.add_argument('-pt', '--peak-threshhold', help='The minimum hight of a detected\
            peak as not to be considered noise', type=int, default=-1)
    parser.add_argument('-act', '--accumulation_time', help='The time the filter accumulates\
            events for to pick the highest signal as "detected Peak",\
            sets the maximum frequency of events that the filter can\
            effectively distinguish', type=int, default=-1)
    parser.add_argument('-ip', help='IP address of the red-pitaya\
            that is connected to the experiment', type=str, default='')
    parser.add_argument('output', help='File to write the data to. The output\
            is a CSV file with one line per event')
    parser.add_argument('config', help='Path to the config file')
    parser.add_argument('-p', '--Port', help='Port of the TCP connection.\
            defaults to 8080', default=8080, type=int)
    parser.add_argument('-hmax', '--histmax', help='maximum pulse height of the\
            pulse height spectrum', type=int, default=18000000)
    parser.add_argument('-hmin', '--histmin', help='minimum pulse height of the\
            pulse height spectrum', type=int, default=500000)
    parser.add_argument('-nplt', '--no-plot', action='store_true', help='disable plotting')

    args = parser.parse_args()
    k, l, m, pthresh, accum_time, ip, port, debug = mbclient.parse_config_from_yml(
            args.config)

    if args.rise_time != -1:
        k = args.rise_time
    if args.hold_time != -1:
        l = args.hold_time
    if args.pulse_decay_time != -1:
        m = args.pulse_decay_time
    if args.peak_threshhold != -1:
        pthresh = args.peak_threshhold
    if args.accumulation_time != -1:
        accum_time = args.accumulation_time
    if args.ip != '':
        ip = args.ip
    if args.Port != -1:
        port = args.Port

    if not debug:
        URI = f'ws://{ip}:{port}/websocket\
?k={k}&l={l}&m={m}&pthresh={pthresh}\
&t_dead={accum_time}'
    else:
        URI = 'ws://localhost:8080'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(mbclient.amain(URI,
                                           args.histmin,
                                           args.histmax,
                                           not args.no_plot,
                                           args.output,
                                           debug))
    pending = asyncio.all_tasks(loop=loop)
    for task in pending:
        task.cancel()
    group = asyncio.gather(*pending, return_exceptions=True)
    loop.run_until_complete(group)
    loop.stop()
    loop.close()


if __name__ == '__main__':
    main()
