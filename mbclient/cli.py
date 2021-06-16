from mbclient import mbclient
import argparse as ap
import asyncio
import sys

debug = False

def main():
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
    parser.add_argument('-plt', '--plot', action='store_true', help='enable plotting')

    args = parser.parse_args()

    if not debug:
        URI = f'ws://{args.IP}:{args.Port}/websocket\
?k={args.K}&l={args.L}&m={args.M}&pthresh={args.peakthresh}\
&t_dead={args.accumtime}'
    else:
        URI = 'ws://localhost:8080'

    loop = asyncio.get_event_loop()
    loop.run_until_complete(mbclient.amain(URI, args))
    pending = asyncio.all_tasks(loop=loop)
    for task in pending:
        task.cancel()
    group = asyncio.gather(*pending, return_exceptions=True)
    loop.run_until_complete(group)
    loop.stop()
    loop.close()


if __name__ == '__main__':
    main()
