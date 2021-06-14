""" This module holds the classes that abstract plotting a histogram
in a different process, as not to slow down the data taking"""
import multiprocessing as mp
import matplotlib.pyplot as plt
import numpy as np

class ProcessPlotter:
    """ Class that holds the environment for the plotting in the different
    process. It is accessed through the NBPlot class from the main process"""
    def __init__(self):
        self.data = []
        self.patches = None
        self.hist = None
        self.hist_values = None
        self.pipe = None
        self.bins = None
        self.fig = None
        self.ax = None

    def call_back(self):
        while self.pipe.poll():
            command = self.pipe.recv()
            if command is None:
                # the plt.close stops the matplotlib event loop
                plt.close('all')
                return False
            tmp_hist, _ = np.histogram(command, self.bins)
            self.hist_values += tmp_hist
            for count, rect in zip(self.hist_values, self.patches):
                rect.set_height(count)
        self.fig.canvas.draw()
        return True

    def __call__(self, pipe, bins):
        """ This is the function that is run in the other process it is called
        at process creation. This is the time where the plot is created.
        When running plt.show() matplotlib starts it's own event loop and calls
        the redraw function 'call_back' every 500 ms."""
        print('starting plotter...')
        self.pipe = pipe
        self.bins = bins
        self.hist_values = np.zeros_like(bins[1:])
        self.fig, self.ax = plt.subplots()
        self.hist, self.bins, self.patches = self.ax.hist([0,], self.bins,
                                                          color='navy')
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
