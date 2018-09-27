# This file was developed by Luke Carroll for the CO880 module at the University of Kent. It is an extension of code
# developed between the Met Office and the National Centre for Atmospheric Science.
#
# This script is intended as a starting point for the development of a GUI to view LIDAR data within the Met Office.
# Various tools have been written to process the data from sample netCDF files and plot it in a useful manner.
# Some of the code is included to demonstrate possible tools that could be used, including possible drawbacks.
# Some particular options are included to show their inappropriateness and should not be run, they have been discussed
# further in the documentation.
#


# pcolor, pcolormesh, contour and contourf all seem relatively capable of plotting the data. My current
# favourite is pcolormesh cause it's faster than some and looks decent. I seem to remember contour not doing
# the colorbar properly.
# If you switch to channel 2 the colorbar doesn't seem to work, I'm not sure why. I should look at the
# channel 2 data.


import lidar
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib import colors, dates, ticker
from datetime import datetime, timezone
import argparse
import re
import warnings
import tkinter as tk
from tkinter import messagebox

PLOT_OPTIONS = {'LINEAR', 'CONTOURF', 'PCOLOR', 'PCOLORMESH'}
VALID_CHANNELS = {0, 1, 2}
time_pattern = re.compile(r"([0-1]?\d|2[0-3]):([0-5]?\d):(\d?\d)")
height_correction = 1.5 * np.arange(12148)


class GuiProcessor:
    """
    A class containing key features for the plotting and manipulation of lidar data.

    """
    def __init__(self, file_path=None, start_string=None, end_string=None,
                 date_string=None, channel=0, plot_choice='PCOLORMESH'):
        """
        The default folder should be 'metoffice-lidar_faam_20150807_r0_B920_raw.nc'
        """
        if file_path is None:
            file_path = 'metoffice-lidar_faam_20150807_r0_B920_raw.nc'

        if date_string is not None and (start_string is None and end_string is None):
            warnings.warn("A date has been provided without any times, the date will be ignored.", Warning)

        self.generate_plot()
        self.lidar_data = lidar.lidar(file_path)
        self.length = self.lidar_data['Time'][:].data.shape[0]

        if date_string is None:
            time_0 = self.lidar_data['Time'][0]
            self.date_dt = datetime.utcfromtimestamp(time_0.item()).date()
        else:
            print("string not none")
            self.date_dt = datetime.strptime(date_string, "%d/%m/%Y").date()
            print(self.date_dt)

        if start_string is None:
            self.start_timestamp = self.lidar_data['Time'][0]
            self.start_moment = 1000
        else:
            self.start_timestamp = self.timestamp_maker(start_string)
            self.start_moment = self.moment_maker(self.start_timestamp)

        if end_string is None:
            self.end_timestamp = self.lidar_data['Time'][-1]
            self.end_moment = 1200
        else:
            self.end_timestamp = self.timestamp_maker(end_string)
            self.end_moment = self.moment_maker(self.end_timestamp)

        if self.start_moment % self.length >= self.end_moment % self.length:
            raise ValueError("End must be greater than start.")

        if plot_choice in PLOT_OPTIONS:
            self.plot_choice = plot_choice
        else:
            raise ValueError(
                "{} is not a valid plot choice. plot_choice must be one of {}.".format(plot_choice, PLOT_OPTIONS))

        if channel in VALID_CHANNELS:
            self.channel = channel
        else:
            raise ValueError("{} is not a valid channel. channel must be one of {}.".format(channel, VALID_CHANNELS))

    # noinspection PyAttributeOutsideInit
    def generate_plot(self):
        """
        Sets up the plotting space.
        """
        # noinspection PyAttributeOutsideInit,PyAttributeOutsideInit
        self.fig, self.ax = plt.subplots()
        plt.subplots_adjust(bottom=0.2)
        # noinspection PyAttributeOutsideInit
        self.callback = Index(self)
        # noinspection PyAttributeOutsideInit
        self.axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
        # noinspection PyAttributeOutsideInit
        self.axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
        # noinspection PyAttributeOutsideInit
        self.bnext = Button(self.axnext, 'Next')
        self.bnext.on_clicked(self.callback.next)
        # noinspection PyAttributeOutsideInit
        self.bprev = Button(self.axprev, 'Previous')
        self.bprev.on_clicked(self.callback.prev)

    def timestamp_maker(self, time_string):
        """

        :param time_string: A string representing a time in the format HH:MM:SS
        :return: The Unix time corresponding to the given string on the date lised at self.date_dt.
        """
        if not isinstance(time_string, str):
            raise TypeError("{} is not a string. Please ensure time_string is a string".format(time_string) +
                            " in the format HH:MM:SS.")
        if not time_pattern.fullmatch(time_string):
            raise ValueError("'{}' is not in the right format. Please ensure time_string is a".format(time_string) +
                             " string in the format HH:MM:SS.")
        time_dt = datetime.strptime(time_string, "%H:%M:%S").time()
        date_dt = self.date_dt
        datetime_dt = datetime.combine(date_dt, time_dt)
        timestamp = datetime.timestamp(datetime_dt.replace(tzinfo=timezone.utc))
        return timestamp

    def moment_maker(self, timestamp):
        """

        :param timestamp: A unix time in the UTC timezone which will be transformed into a moment
        within the LIDAR experiment.
        :return: A moment in the experiment corresponding to the unix time.
        """
        time_array = self.lidar_data['Time'][:].data
        if timestamp < time_array.min():
            # print(str(timestamp) + " < " + str(time_array.min()))
            warnings.warn("A given date and time is earlier "
                          "than the experiment period", Warning)
            return 0
        elif timestamp > time_array.max():
            warnings.warn("A given date and time is later "
                          "than the experiment period", Warning)
            return -1
        else:
            index_array = np.argwhere(time_array <= timestamp)
            index = index_array.max()
            return index

    def start_end_maker(self, start_string, end_string):
        if not isinstance(start_string, str):
            raise TypeError("{} is not a string. Please ensure start_string is a string".format(start_string) +
                            " in the format HH:MM:SS.")
        if not time_pattern.fullmatch(start_string):
            raise ValueError("'{}' is not in the right format. Please ensure start_string is a".format(start_string) +
                             " string in the format HH:MM:SS.")
        if not isinstance(end_string, str):
            raise TypeError("{} is not a string. Please ensure end_string is a string".format(end_string) +
                            " in the format HH:MM:SS.")
        if not time_pattern.fullmatch(end_string):
            raise ValueError("'{}' is not in the right format. Please ensure end_string is a".format(end_string) +
                             " string in the format HH:MM:SS.")
        start_timestamp = self.timestamp_maker(start_string)
        print(start_timestamp)
        end_timestamp = self.timestamp_maker(end_string)
        print(end_timestamp)
        start = self.moment_maker(start_timestamp)
        end = self.moment_maker(end_timestamp)
        return start, end

    def z_maker(self, x=None, y=None, channel=None):
        """"
        using the mask option might avoid misrepresenting data, but it causes some warnings when using
        pcorlormeshthe warnings don't seem to happen with pcorlor, not sure about contourf
        """
        if x is None:
            x = self.start_moment
        if y is None:
            y = self.end_moment
        if channel is None:
            channel = self.channel
        data = self.lidar_data.profile[channel][x:y].data.clip(0)
        data_m = ma.masked_invalid(data)
        return data_m

    def height_maker(self, x, y, z):
        """
        When the altitude is not defined it is set to 0. This is to prevent some world stopping errors.
        It can make some of the data look odd. But for the most part it will have the desired effect of hiding data
        without a defined height. The alternative is to mask the height and this works fine for contourf. However
        simply masking the array results in pcolor or pcolormesh crashing pcolormesh seems to be the fasted way to plot
        hence my decision.
        :param x: The start moment of the sample.
        :param y: The end moment of the sample.
        :param z: The lidar data who's shape the result will be based on.
        :return: A numpy array of heights of the same shape as a a provided array of LIDAR data.
        """
        altitude = self.lidar_data['Altitude (m)'][x:y].data
        height_array = np.empty_like(z)
        for j in range(0, len(z[0])):
            height_array[:, j] = altitude[j] - height_correction
        height_array = np.nan_to_num(height_array.clip(0))
        return height_array

    def time_maker(self, x, y, z):
        """
        This method is only really used with contouf. It can be used with pcolormesh but does not have to be.
        :param x: The start moment of the sample.
        :param y: The end moment of the sample.
        :param z: The lidar data who's shape the result will be based on.
        :return: A numpy array of times of the same shape as a a provided array of LIDAR data.
        """
        time = self.lidar_data['Time'][x:y].data
        time_array = np.empty_like(z)
        for j in range(0, len(z)):
            for i in range(0, len(z[j])):
                time_array[j, i] = time[i]
        mpl_time = dates.epoch2num(time_array)
        return mpl_time

    # contour and contourf are slow and contour leaves white space
    # pcolor is slow
    def plotter(self, start_moment=None, end_moment=None, channel=0, plot_choice="PCOLORMESH"):
        """
        Pcolor is slow.
        :param start_moment: Start moment
        :param end_moment: End moment
        :param channel: THe LIDAR channel
        :param plot_choice: What method should be used to plot
        :return: Plots the graph
        """
        if plot_choice not in PLOT_OPTIONS:
            raise ValueError("plot_choice must be one of {}.".format(PLOT_OPTIONS))
        if channel not in VALID_CHANNELS:
            raise ValueError("channel must be one of {}.".format(VALID_CHANNELS))

        length = self.lidar_data['Time'][:].data.shape[0]
        if start_moment is None:
            start_moment = self.start_moment
        if end_moment is None:
            end_moment = self.end_moment
        if start_moment % length >= end_moment % length:
            raise ValueError("End must be greater than start.")

        self.ax.cla()
        plt.sca(self.ax)

        z = self.z_maker(start_moment, end_moment, channel)
        time = dates.epoch2num(self.lidar_data['Time'][start_moment:end_moment].data)
        altitude = self.lidar_data['Altitude (m)'][start_moment:end_moment].data
        height = self.height_maker(start_moment, end_moment, z)

        if ~np.isnan(np.nanmax(altitude)):
            plt.ylim(0, np.nanmax(altitude) * 1.1)

        plt.ylabel('Height (m)')
        plt.xlabel('Time')

        if plot_choice == "PCOLOR":
            print("It is pcolor")
            contour_p = plt.pcolor(time, height, z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))
        elif plot_choice == "LINEAR":
            print("It is linear")
            contour_p = plt.pcolormesh(time, height, z, vmax=0.0007)
        elif plot_choice == "CONTOURF":
            print("It is contourf")
            time_tall = self.time_maker(start_moment, end_moment, z)
            contour_p = plt.contourf(time_tall, height, z, locator=ticker.LogLocator())
        else:
            print("It is log")
            contour_p = plt.pcolormesh(time, height, z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))

        line_p = plt.plot(time, altitude, color='black', linewidth=2)
        my_fmt = dates.DateFormatter('%H:%M')
        self.ax.xaxis.set_major_formatter(my_fmt)
        # noinspection PyAttributeOutsideInit
        self.cb = plt.colorbar(contour_p)


class Index(object):
    def __init__(self, processor):
        self.processor = processor

    def next(self, event):
        if (self.processor.end_moment % self.processor.length) >= (self.processor.length - 1):
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning('End of Data', "You have reached the end of the data.")
            # win32api.MessageBox(0, 'You have reache
            # d the end of the data.', 'End of Data')
        else:
            # self.processor = processor
            if self.processor.length - 1 > self.processor.end_moment % self.processor.length > self.processor.length - 101:
                self.processor.start_moment = (self.processor.start_moment % self.processor.length) + \
                                              ((self.processor.length - 1) - (
                                                          self.processor.end_moment % self.processor.length))
                self.processor.end_moment = self.processor.length - 1
            else:
                self.processor.start_moment = self.processor.start_moment % self.processor.length + 100
                self.processor.end_moment = self.processor.end_moment % self.processor.length + 100
            self.processor.cb.remove()
            self.processor.plotter(plot_choice=self.processor.plot_choice, channel=self.processor.channel)
            plt.draw()

    def prev(self, event):
        # self.processor = processor
        if (self.processor.start_moment % self.processor.length) <= 0:
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning('End of Data', "You have reached the end of the data.")
            # win32api.MessageBox(0, 'You have reached the end of the data.', 'End of Data')
        else:
            if 0 < self.processor.start_moment % self.processor.length < 100:
                self.processor.end_moment = (self.processor.end_moment % self.processor.length) - \
                                            (self.processor.start_moment % self.processor.length)
                self.processor.start_moment = 0
            else:
                self.processor.start_moment = self.processor.start_moment % self.processor.length - 100
                self.processor.end_moment = self.processor.end_moment % self.processor.length - 100
            self.processor.cb.remove()
            self.processor.plotter(plot_choice=self.processor.plot_choice, channel=self.processor.channel)
            plt.draw()


def time_type(s):
    """
    This is a data type to ensure users enter the time correctly.
    """
    if not time_pattern.fullmatch(s):
        raise argparse.ArgumentTypeError("Please enter a valid time in the format HH:MM:SS.")
    return s


def date_type(s):
    """
    This is a data type to ensure users enter the date correctly. It cannot currently account for leap years.
    """
    pat = re.compile(r"^(((0?[1-9]|[1-2]\d|3[0-1])/(0?[1,3,5,7,8]|1[0,2]))"
                     r"|((0?[1-9]|[1-2]\d|30)/(0?[4,6,9]|11))"
                     r"|((0?[1-9]|[1-2]\d)/(0?2)))"
                     r"/\d\d\d\d$")
    if not pat.fullmatch(s):
        raise argparse.ArgumentTypeError("Please enter a valid date in the format DD/MM/YYYY.")
    return s


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Enter values for LIDAR processing.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--start', type=time_type, default=None, help='the start time in the format HH:MM:SS')
    parser.add_argument('--end', type=time_type, default=None, help='the end time in the format HH:MM:SS')
    parser.add_argument('--date', type=date_type, default=None, help='the date time in the format DD/MM/YYYY')
    parser.add_argument('--plot_choice', type=str, choices=PLOT_OPTIONS, default='PCOLORMESH',
                        help='Which plot do you want')
    parser.add_argument('--channel', type=int, choices=VALID_CHANNELS, default=0,
                        help='Which LIDAR channel do you want data from?')
    parser.add_argument('--file_path', type=str, default=None,
                        help='Enter the path to the NetCDF file containing the LIDAR data.')

    args = parser.parse_args()
    file_path = args.file_path
    date_string = args.date
    start_string = args.start
    end_string = args.end
    plot_choice = args.plot_choice
    channel = args.channel

    #    def __init__(self, file_path='metoffice-lidar_faam_20150807_r0_B920_raw.nc', start_string=None, end_string=None,
    # date_string=None, channel=0):

    processor = GuiProcessor(file_path=file_path, start_string=start_string, end_string=end_string,
                             date_string=date_string, channel=channel, plot_choice=plot_choice)
    processor.plotter(channel=channel, plot_choice=plot_choice)

    print("Near the end")
    plt.show()
