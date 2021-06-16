""" This module holds the classes that abstract plotting a histogram
in a different process, as not to slow down the data taking"""
import multiprocessing as mp
import matplotlib.pyplot as plt
import numpy as np


class ProcessPlotter:
    """ Class that holds the environment for the plotting in the different
    process. It is accessed through the NBPlot class from the main process"""
    def __init__(self, low_peak_thresh, high_peak_thresh):
        self.data = []
        self.patches = None
        self.hist = None
        self.pipe = None
        self.fig = None
        self.ax1 = None
        self.ax2 = None
        self.quad = None
        bin_amount = int(np.ceil((high_peak_thresh - low_peak_thresh)/35000))
        self.ybins = np.linspace(low_peak_thresh, high_peak_thresh, bin_amount)
        self.xbins = np.linspace(0, 1023, 128)
        self.hist_values = np.zeros_like(self.ybins[:-1])
        self.xcenters = (self.xbins[1:] + self.xbins[:-1])/2
        self.ycenters = (self.ybins[1:] + self.ybins[:-1])/2
        self.y, self.x = np.meshgrid(self.xcenters, self.ycenters)
        self.hist2d = np.zeros_like(self.x)

    def process_for_peak_height_hist(self, data):
        delta_hist, _ = np.histogram([e.peak_height for e in data],
                                     bins=self.ybins)
        return delta_hist

    def process_for_2d_hist(self, data):
        ydata = [e.peak_height for e in data]
        xdata = [e.speed for e in data]
        deltahist, _, _ = np.histogram2d(ydata, xdata,
                                         bins=(self.ybins, self.xbins))
        return deltahist

    def call_back(self):
        while self.pipe.poll():
            command = self.pipe.recv()
            if command is None:
                # the plt.close stops the matplotlib event loop
                plt.close('all')
                return False
            # we have gotten a valid data package so lets pass it into the
            self.hist_values += self.process_for_peak_height_hist(command)
            self.ax1.set_ylim(0, max(self.hist_values)+100)
            self.hist2d += self.process_for_2d_hist(command)
            self.quad.set_clim(0, max(self.hist2d.ravel()) + 2)
            for count, rect in zip(self.hist_values, self.patches):
                rect.set_height(count)
            self.quad.set_array(self.hist2d.ravel())
        self.fig.canvas.draw()
        return True

    def __call__(self, pipe):
        """ This is the function that is run in the other process it is called
        at process creation. This is the time where the plot is created.
        When running plt.show() matplotlib starts it's own event loop and calls
        the redraw function 'call_back' every 500 ms."""
        print('starting plotter...')
        self.pipe = pipe
        self.fig, axes = plt.subplots(2)
        self.ax1 = axes[0]
        self.ax2 = axes[1]
        self.hist, _, self.patches = self.ax1.hist([], bins=self.ybins,
                                                          color='navy')
        self.quad = self.ax2.pcolormesh(self.x,
                                        self.y,
                                        self.hist2d,
                                        shading='gouraud',
                                        vmax=5)
        self.ax1.set_ylim(0, 300)
        self.ax1.set_xlim(self.ybins[0], self.ybins[-1])
        self.ax1.set_xlabel(r'Pulshoehe $\propto$ Energie')
        self.ax1.set_ylabel('Ereignisanzahl')
        self.ax1.grid()
        self.ax1.set_title('Pulshoehenspektrum')
        self.ax2.set_ylabel(r'DFG-Addresse')
        self.ax2.set_xlabel(r'Pulshoehe $\propto$ Energie')
        self.ax2.grid()
        timer = self.fig.canvas.new_timer(interval=1000)
        timer.add_callback(self.call_back)
        timer.start()
        plt.show()


class NBPlot:
    def __init__(self, low_peak_thresh, high_peak_thresh):
        self.plot_pipe, plotter_pipe = mp.Pipe()
        self.plotter = ProcessPlotter(low_peak_thresh, high_peak_thresh)
        self.plot_process = mp.Process(target=self.plotter,
                                       args=(plotter_pipe,), daemon=True)
        self.plot_process.start()
        self.joined = False
    def plot(self, data=None, finished=False):
        if self.plot_process.is_alive():
            send = self.plot_pipe.send
            if finished:
                data = None
            try:
                send(data)
            except (BrokenPipeError, ConnectionResetError):
                print("The plotter was closed")
                self.plot_pipe.close()
                self.plot_process.join()
                self.joined = True
        elif not self.joined:
            self.plot_pipe.close()
            self.plot_process.join()
            self.joined = True

