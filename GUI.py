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
# This regular expression can be used to ensure a string represents a proper time in the 24 hour clock with the
# time being written in the format HH:MM:SS
time_pattern = re.compile(r"([0-1]?\d|2[0-3]):([0-5]?\d):(\d?\d)")
# This 'height correction' is based off of information provided by Dave Tiddeman at the Met Office. Each pulse
# in a LIDAR profile is fired "10 nanoseconds later or 1.5 meters further from the aircraft". As such to find the
# height for a LIDAR point I must incrementally cubtract 1.5m from the altitude of the plane.
height_correction = 1.5 * np.arange(12148)


class GuiProcessor:
    """
    This class contains numerous method for handling LIDAR data and getting it ready to be plotted.
    It's main purpose is to produce a plot using the plotter() method, however some of the methods are useful for
    manipulating anf viewing the LIDAR data in and of itself.



    """
    def __init__(self, file_path=None, start_string=None, end_string=None,
                 date_string=None, channel=0, plot_choice='PCOLORMESH'):
        """
        This method creates the processor while checking that the values being used make sense.

        :param file_path: The file path to the sample data, if none is provided it will be changed to
                            'metoffice-lidar_faam_20150807_r0_B920_raw.nc'
        :param start_string: A string representing the start time in the format HH:MM:SS.
        :param end_string: A string representing the end time in the format HH:MM:SS.
        :param date_string: A string representing the date of the data in the format DD/MM/YYYY. With the files
                            available this choice does not change much. Both sample files represent data from a
                            single day, the date of which is automatically chosen if the string is left blank. Hence,
                            choosing a different date would simply cause an error. This option was included, to account
                            for the possibility that other files might require a date choice.

        :param channel: The channel from the LIDAR tool from which data should be taken. The channels can be 0, 1 or 2.
                        Only the LIDAR data itself is affect, height, time and altitude will not change.

        :param plot_choice: Represents the tool that should be used to plot the LIDAR data. This was included to show
                            each methods capabilities. The options are:
                            PCOLORMESH - Which represents plotting using the pcolormesh method and a logarithmic scale.
                            LINEAR - Which represents plotting using the pcolormesh method and a linear scale.
                            CONTOURF - Which represents plotting using the contourf method and a logarithmic scale.
                                       When this option is used the Next and Previous buttons do not function properly.
                            PCOLOR - Which represents plotting using the pcolor method and a logarithmic scale. This
                                     method takes a long time to plot; it takes around 50 seconds to plot a 7 minute
                                     interval (which is the default size). It is not recommended for larger intervals
                                     or using with the Next and Previous button.
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
            self.date_dt = datetime.strptime(date_string, "%d/%m/%Y").date()

        if start_string is None:
            self.start_timestamp = self.lidar_data['Time'][1000]
            self.start_moment = 1000
        else:
            self.start_timestamp = self.timestamp_maker(start_string)
            self.start_moment = self.moment_maker(self.start_timestamp)

        if end_string is None:
            self.end_timestamp = self.lidar_data['Time'][1200]
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

    def generate_plot(self):
        """
        This sets up a figure and subplot which data which will be plotted onto either. It also creates the Next
        and Previous button. Most of this code was adapted from https://matplotlib.org/examples/widgets/buttons.html
        """
        self.fig, self.ax = plt.subplots()
        plt.subplots_adjust(bottom=0.2)
        self.callback = Index(self)
        self.axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
        self.axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
        self.bnext = Button(self.axnext, 'Next')
        self.bnext.on_clicked(self.callback.next)
        self.bprev = Button(self.axprev, 'Previous')
        self.bprev.on_clicked(self.callback.prev)

    def timestamp_maker(self, time_string):
        """
        This method takes a string in the format HH:MM:SS and returns a standard Unix timestamp corresponding
        to that time on the date listed at self.date_dt. The timezone is assumed to be UTC.

        :param time_string: A string representing a time in the format HH:MM:SS
        :return: The Unix timestamp corresponding to the given string on the date listed at self.date_dt.
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
        This method takes a standard Unix timestamp and returns the index of that time within the LIDAR data. If the
        timestamp is set before the experiment began it is set to the first moment in the experiment. If the timestamp
        is set after the experiment is finished, then it is set to the last moment. The timezone is assumed to be UTC.

        :param timestamp: A unix timestamp in the UTC timezone which will be transformed into a moment
        within the LIDAR experiment.
        :return: A moment in the experiment corresponding to the unix timestamp.
        """
        time_array = self.lidar_data['Time'][:].data
        if timestamp < time_array.min():
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

    def z_maker(self, start_moment=None, end_moment=None, channel=None):
        """
        This method produces and array of LIDAR data between the start moment and the end moment. Note that nan values
        will be masked. Some plotting options struggle with masked values and might throw warnings.

        :param start_moment: The start index for filtering te LIDAR data.
        :param end_moment: The start index for filtering te LIDAR data.
        :param channel: The LIDAR chanel from which data will be taken.
        :return: An array of LIDAR data with nan values masked and any value below 0 set to 0.
        """
        if start_moment is None:
            start_moment = self.start_moment
        if end_moment is None:
            end_moment = self.end_moment
        if channel is None:
            channel = self.channel
        if channel not in VALID_CHANNELS:
            raise ValueError("{} is not a valid channel. channel must be one of {}.".format(channel, VALID_CHANNELS))
        data = self.lidar_data.profile[channel][start_moment:end_moment].data.clip(0)
        data_m = ma.masked_invalid(data)
        return data_m

    def height_maker(self, start_moment, end_moment, z):
        """
        This method creates a returns an array of heights of the same shape as a given LIDAR data array. The reasoning
        behind subtracting height_correction from altitude is established at the top of this file. When the Altitude
        is not defined the height is set to 0. This is because several of the plotting methods, including the default
        PCOLORMESH cannot handle masked or nan values in an axis like height. This compromise can result in some
        sections slightly misrepresenting the data. However, none of the methods I'vr found can handle a masked height,
        certainly not within a reasonable time. For the most part setting the height has a reasonable effect of hiding
        the data in this undefined region.

        :param start_moment: The start moment of the sample.
        :param end_moment: The end moment of the sample.
        :param z: The lidar data who's shape the result will be based on.
        :return: A numpy array of heights of the same shape as a a provided array of LIDAR data.
        """
        altitude = self.lidar_data['Altitude (m)'][start_moment:end_moment].data
        height_array = np.empty_like(z)
        for j in range(0, len(z[0])):
            height_array[:, j] = altitude[j] - height_correction
        height_array = np.nan_to_num(height_array.clip(0))
        return height_array

    def time_maker(self, start_moment, end_moment, z):
        """
        This method produces an array of Unix timestamps of the same shape as some provided LIDAR data. Some of the
        plotting methods can use time in this shape, however only contour and contourf seem to require it.

        :param start_moment: The start moment of the sample.
        :param end_moment: The end moment of the sample.
        :param z: The lidar data who's shape the result will be based on.
        :return: A numpy array of times of the same shape as a a provided array of LIDAR data.
        """
        time = self.lidar_data['Time'][start_moment:end_moment].data
        time_array = np.empty_like(z)
        for j in range(0, len(z)):
            for i in range(0, len(z[j])):
                time_array[j, i] = time[i]
        mpl_time = dates.epoch2num(time_array)
        return mpl_time

    def plotter(self, start_moment=None, end_moment=None, channel=0, plot_choice="PCOLORMESH"):
        """
        This method takes information provided to it or taken from the GuiProcessor class and turns it into a
        plotted figure. The default tool used for plotting is PCOLORMESH. PCOLORMESH seems to be the quickest and
        produces a reasonable looking plot using a logarithmic scale. Other options are available, however
        they can have serious drawbacks, as explained under the plot)choice parameter.

        :param start_moment: The index within the LIDAR data the method starts plotting from.
        :param end_moment: The end index of the plot.
        :param channel: The channel from the LIDAR tool from which data should be taken. The channels can be 0, 1 or 2.
                        Only the LIDAR data itself is affect, height, time and altitude will not change.

        :param plot_choice: Represents the tool that should be used to plot the LIDAR data. This was included to show
                            each methods capabilities. The options are:
                            PCOLORMESH - Which represents plotting using the pcolormesh method and a logarithmic scale.
                            LINEAR - Which represents plotting using the pcolormesh method and a linear scale.
                            CONTOURF - Which represents plotting using the contourf method and a logarithmic scale.
                                       When this option is used the Next and Previous buttons do not function properly.
                            PCOLOR - Which represents plotting using the pcolor method and a logarithmic scale. This
                                     method takes a long time to plot; it takes around 50 seconds to plot a 7 minute
                                     interval (which is the default size). It is not recommended for larger intervals
                                     or using with the Next and Previous button.
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
            contour_p = plt.pcolor(time, height, z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))
        elif plot_choice == "LINEAR":
            contour_p = plt.pcolormesh(time, height, z, vmax=0.0007)
        elif plot_choice == "CONTOURF":
            time_tall = self.time_maker(start_moment, end_moment, z)
            contour_p = plt.contourf(time_tall, height, z, locator=ticker.LogLocator())
        else:
            contour_p = plt.pcolormesh(time, height, z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))

        line_p = plt.plot(time, altitude, color='black', linewidth=2)
        my_fmt = dates.DateFormatter('%H:%M')
        self.ax.xaxis.set_major_formatter(my_fmt)
        self.cb = plt.colorbar(contour_p)


class Index(object):
    """
    This class provides the functionality for the Next and Previous button in the GUI. The structure of this
    class was taken from https://matplotlib.org/examples/widgets/buttons.html
    """
    def __init__(self, processor):
        self.processor = processor

    def next(self, event):
        """
        This method is assigned to the Next button. When pressed it moves the data along 100 "moments". This usually
        corresponds to around 3.5 minutes. If the data is within 100 moments of the end, then it simply goes up to
        the very end and stops. Any attempts to move further will results in a warning message being displayed.
        :param event: Clicking Next
        """
        if (self.processor.end_moment % self.processor.length) >= (self.processor.length - 1):
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning('End of Data', "You have reached the end of the data.")

        else:
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
        """
        This method is assigned to the Previous button. When pressed it moves the data back 100 "moments". This usually
        corresponds to around 3.5 minutes. If the data is within 100 moments of the beginning, then it simply goes back
        to the very beginning and stops. Any attempts to move further back will results in a warning message being
        displayed.
        :param event: Clicking Previous
        """
        if (self.processor.start_moment % self.processor.length) <= 0:
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning('End of Data', "You have reached the end of the data.")
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
    This is a data type to ensure users enter the time in the format HH:MM:SS.
    """
    if not time_pattern.fullmatch(s):
        raise argparse.ArgumentTypeError("Please enter a valid time in the format HH:MM:SS.")
    return s


def date_type(s):
    """
    This is a data type to ensure users enter the date in the format DD/MM/YYYY. This method currently allows 29
    February as a valid date even in years that are not leap years.
    The first line in the pattern represents that January, March, May, July, August, October and December can have a
    day between 1 and 31.
    The second line represents that April, June, September and November can have a day between 1 and 30.
    The third line represents that February can have a day between 1 and 29.
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

    processor = GuiProcessor(file_path=file_path, start_string=start_string, end_string=end_string,
                             date_string=date_string, channel=channel, plot_choice=plot_choice)
    processor.plotter(channel=channel, plot_choice=plot_choice)
    plt.show()