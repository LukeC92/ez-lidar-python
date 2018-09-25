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
from datetime import datetime, time, timezone
import argparse
import re
import warnings


# lidar_data = lidar.lidar('metoffice-lidar_faam_20150807_r0_B920_raw.nc')
# time_0 = lidar_data['Time'][0]
# date = datetime.utcfromtimestamp(time_0.item())
# start_moment = 200
# end_moment = 400
PLOT_OPTIONS =  {'LINEAR', 'CONTOURF', 'PCOLOR', 'PCOLORMESH'}
VALID_CHANNELS = {0, 1, 2}
time_pattern = re.compile(r"([0-1]?\d|2[0-3]):([0-5]?\d):(\d?\d)")

# m_time = dates.epoch2num(lidar_data['Time'][:].data)
# full_altitude = lidar_data['Altitude (m)'][:].data
height_correction = 1.5 * np.arange(12148)

class GUI_processor:
    def __init__(self, file_path='metoffice-lidar_faam_20150807_r0_B920_raw.nc', start_string=None, end_string=None,
                 date_string=None, channel=0):
        """
        The default folder should be 'metoffice-lidar_faam_20150807_r0_B920_raw.nc'
        """
        self.lidar_data = lidar.lidar(file_path)
        if date_string == None:
            print("String was none")
            time_0 = self.lidar_data['Time'][0]
            self.date_dt = datetime.utcfromtimestamp(time_0.item())
        else:
            self.date_dt = datetime.strptime(date_string, "%d/%m/%Y")
            print("String was not none.")

        if start_string == None:
            print("start String was none")
            self.start_epoch = self.lidar_data['Time'][0]
            self.start_moment = 1000
        else:
            self.start_epoch = self.epoch_maker(start_string)
            self.start_moment = self.moment_maker(self.start_epoch)
            print("start String was not none.")

        if end_string == None:
            print("End String was none")
            end_epoch = self.lidar_data['Time'][-1]
            self.end_moment = 1200
        else:
            end_epoch = self.epoch_maker(end_string)
            self.end_moment = self.moment_maker(end_epoch)
            print("End String was not none.")

        length = self.lidar_data['Time'][:].data.shape[0]
        print(length)
        print("Start is" + str(self.start_moment))
        print("Start modulo is " + str(self.start_moment % length))
        print("End is" + str(self.end_moment))
        print("End modulo is " + str(self.end_moment % length))
        if self.start_moment % length >= self.end_moment % length:
            raise ValueError("End must be greater than start.")

        if channel in VALID_CHANNELS:
            self.channel = channel
        else:
            raise ValueError("channel must be one of {}.".format(VALID_CHANNELS))

    def generatePlot(self):
        self.fig, self.ax = plt.subplots()
        plt.subplots_adjust(bottom=0.2)
        self.callback = Index()
        self.axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
        self.axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
        self.bnext = Button(self.axnext, 'Next')
        self.bnext.on_clicked(self.callback.next)
        self.bprev = Button(self.axprev, 'Previous')
        self.bprev.on_clicked(self.callback.prev)

    def z_maker(self, x=None, y=None, channel=None):
        """"
        using the mask option might avoid misrepresenting data, but it causes some warnings when using
        pcorlormeshthe warnings don't seem to happen with pcorlor, not sure about contourf
        """
        if x == None:
            x = self.start_moment
        if y == None:
            y = self.end_moment
        if channel == None:
            channel = self.channel
        data = self.lidar_data.profile[channel][x:y].data.clip(0)
        data_m = ma.masked_invalid(data)
        return data_m
        # return np.nan_to_num(lidar_data.profile[channel][x:y].data.clip(0))

    def height_maker(self, x, y, z):
        """

        :param x: The start moment of the sample.
        :param y: The end moment of the sample.
        :param z: The lidar data who's shape the result will be based on.
        :return: A numpy array of heights of the same shape as a a provided array of LIDAR data.
        """
        altitude = self.lidar_data['Altitude (m)'][x:y].data
        # altitude = full_altitude[x:y]
        altitude_array = np.empty_like(z)
        for j in range(0, len(z[0])):
            altitude_array[:, j] = altitude[j] - height_correction
        altitude_array = np.nan_to_num(altitude_array.clip(0))
        # altitude_array = altitude_array.clip(0)
        # height = ma.masked_invalid(altitude_array)
        return altitude_array

    def time_maker(self, x, y, z):
        """

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

    def moment_maker(self, epoch_time):
        """

        :param epoch_time: A unix time in the UTC timezone which will be transformed into a moment
        within the LIDAR experiment.
        :return: A moment in the experiment corresponding to the unix time.
        """
        time_array = self.lidar_data['Time'][:].data
        if epoch_time < time_array.min():
            print(str(epoch_time) + " < " + str(time_array.min()))
            warnings.warn("A given date and time is earlier "
                          "than the experiment period", Warning)
            return 0
        elif epoch_time > time_array.max():
            print(str(epoch_time) + " > " + str(time_array.max()))
            warnings.warn("A given date and time is later "
                          "than the experiment period", Warning)
            return -1
        else:
            index_array = np.argwhere(time_array <= epoch_time)
            index = index_array.max()
            return index

    def epoch_maker(self, time_string):
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
        start_e = self.epoch_maker(start_string)
        end_e = self.epoch_maker(end_string)
        print("Start is " + str(start_e))
        print("End is " + str(end_e))
        start = self.moment_maker(start_e)
        end = self.moment_maker(end_e)
        return (start, end)

    # contour and contourf are slow and contour leaves white space
    # pcolor is slow
    def plotter(self, start=None, end=None, channel=0, plot_choice="PCOLORMESH"):
        """

        :param start: Start moment
        :param end: End moment
        :param channel: THe LIDAR channel
        :param plot_choice: What method should be used to plot
        :return: Plots the graph
        """
        # if cb != None:
        #     cb.remove()
        if plot_choice not in PLOT_OPTIONS:
            raise ValueError("plot_choice must be one of {}.".format(PLOT_OPTIONS))
        if channel not in VALID_CHANNELS:
            raise ValueError("channel must be one of {}.".format(VALID_CHANNELS))

        # # pcolor and pcolormesh could use time_tall
        # (start, end) = start_end_maker(start_time, end_time)
        # # start = start_end[0]
        # # end = start_end[1]
        length = self.lidar_data['Time'][:].data.shape[0]
        # ask on stack overflow if there's a more effecient way of doing this

        # start = start_moment
        # # end = end_moment

        if start == None:
            start = self.start_moment
        if end == None:
            end = self.end_moment
        if start % length >= end % length:
            raise ValueError("End must be greater than start.")
        #plt.gcf()
        self.fig
        self.ax.cla()
        plt.sca(self.ax)

        #ax = plt.axes()

        z =  self.z_maker(start, end, channel)
        time = dates.epoch2num(self.lidar_data['Time'][start:end].data)
        altitude = self.lidar_data['Altitude (m)'][start:end].data
        # altitude = full_altitude[start:end]
        height = self.height_maker(start, end, z)
        # height = height_quick_maker(start, end)
        if ~np.isnan(np.nanmax(altitude)):
            plt.ylim(0, np.nanmax(altitude) * 1.1)
        plt.ylabel('Height (m)')
        plt.xlabel('Time')
        print(plot_choice)
        if plot_choice == "PCOLOR":
            print("It is pcolor")
            contour_p = plt.pcolor(time, height, z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))
        elif plot_choice == "LINEAR":
            print("It is linear")
            contour_p = plt.pcolormesh(time, height, z, vmax=0.0007)
        elif plot_choice == "CONTOURF":
            print("It is contourf")
            time_tall = self.time_maker(start, end, z)
            contour_p = plt.contourf(time_tall, height, z, locator=ticker.LogLocator())
        else:
            print("It is log")
            contour_p = plt.pcolormesh(time, height, z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))
        line_p = plt.plot(time, altitude, color='black', linewidth=2)
        myFmt = dates.DateFormatter('%H:%M')
        self.ax.xaxis.set_major_formatter(myFmt)
        self.cb = plt.colorbar(contour_p)


class Index(object):
    def next(self, event):
        #print(ax.xaxis)
        print('start')
        processor.cb.remove()
        # print(contour_p.get_array())
        #plt.clf()
        # fig = processor.fig
        # im = fig.images
        # cb = im[0].colorbar
        # cb.remove()
        print(processor.start_moment)
        print(processor.end_moment)
        processor.start_moment += 100
        processor.end_moment += 100
        print(processor.start_moment)
        print(processor.end_moment)
        plt.gcf()

        #fig, ax = plt.subplots()
        plt.subplots_adjust(bottom=0.2)
        processor.plotter()

        # processor.plotter(start_string, end, channel=channel, plot_choice=plot_choice)
        # callback = Index()
        # axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
        # axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
        # bnext = Button(axnext, 'Next')
        # bnext.on_clicked(callback.next)
        # bprev = Button(axprev, 'Previous')
        # bprev.on_clicked(callback.prev)

        print("Near the end")
        plt.draw()
        # plt.cla() just clears the button
        # https://stackoverflow.com/questions/17085711/plot-to-specific-axes-in-matplotlib
        # https://stackoverflow.com/questions/14254379/how-can-i-attach-a-pyplot-function-to-a-figure-instance/14261698#14261698
        # could those links help?
        # start = 2000
        # end = 2200
        # start += 100
        # end += 100
        # z_test = z_maker(start, end)
        # time_test = datetime_array[start:end]
        # height_test = height_quick_maker(start, end)
        # c = plt.pcolormesh(time_test,height_test,z_test, norm=colors.LogNorm(vmin=0.000001, vmax=z_test.max()))
        # plt.colorbar(c)
        # plt.draw()

    def prev(self, event):
        print("Testing testing 123")

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
    parser.add_argument('--start', type=time_type,
                        default=None, help='the start time in the format HH:MM:SS')
    parser.add_argument('--end', type=time_type,
                        default=None, help='the end time in the format HH:MM:SS')
    parser.add_argument('--date', type=date_type,
                        default=None, help='the date time in the format DD/MM/YYYY')
    parser.add_argument('--plot_choice', type=str, choices=PLOT_OPTIONS,
                        default='PCOLORMESH', help='Which plot do you want')
    parser.add_argument('--channel', type=int, choices=VALID_CHANNELS,
                        default=0, help='Which LIDAR channel do you want data from?')
    parser.add_argument('--file_path', type=str, default='metoffice-lidar_faam_20150807_r0_B920_raw.nc',
                        help='Enter the path to the NetCDF file containing the LIDAAR data.')

    args = parser.parse_args()
    file_path = args.file_path
    date_string = args.date
    start_string = args.start
    end_string = args.end
    plot_choice = args.plot_choice
    channel = args.channel





    #
    # print(start_string < end)
    #
    # if end < start_string:
    #     raise ValueError("Start must come before end.")

    # fig, ax = plt.subplots()
    # plt.subplots_adjust(bottom=0.2)

    processor = GUI_processor(start_string=start_string, end_string=end_string)
    processor.generatePlot()
    processor.plotter()

    # processor.plotter(start_string, end, channel=channel, plot_choice=plot_choice)
    # callback = Index()
    # axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
    # axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    # bnext = Button(axnext, 'Next')
    # bnext.on_clicked(callback.next)
    # bprev = Button(axprev, 'Previous')
    # bprev.on_clicked(callback.prev)

    print("Near the end")
    plt.show()

#     (gradLi2)
#     C:\Users\lukec\OneDrive\Documents\GitHub\ez - lidar - python > python
#     GUI.py - -start
#     "14:00:00" - -end
#     "14:30:00"
#     ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattr__',
#      '__getattribute__', '__getitem__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__',
#      '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__',
#      '__str__', '__subclasshook__', '__weakref__', '_range_correction', '_trigger', '_view', 'add_raw', 'aux', 'create',
#      'createCurtainNC', 'fltno', 'get_aux', 'get_img', 'get_prof', 'get_ratio', 'get_raw_indexes', 'get_rc',
#      'get_rc_corr', 'getprofile', 'make_curtain', 'make_img', 'make_jpg', 'maxheight', 'merge_aux', 'ncfolder',
#      'range_correction', 'rawfolder', 'rc_div', 'rebuild_raw', 'trigger', 'view', 'write_dims', 'write_time']
#     {}
#     String
#     was
#     none
#     start
#     String
#     was
#     not none.
#     End
#     String
#     was
#     not none.
#     Traceback(most
#     recent
#     call
#     last):
#     File
#     "GUI.py", line
#     295, in < module >
#     processor = GUI_processor(start_string=start_string, end_string=start_string)
# File
# "GUI.py", line
# 67, in __init__
# raise ValueError("End must be greater than start.")
# ValueError: End
# must
# be
# greater
# than
# start.
#
# (gradLi2)
# C:\Users\lukec\OneDrive\Documents\GitHub\ez - lidar - python >