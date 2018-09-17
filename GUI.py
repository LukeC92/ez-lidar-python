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


lidar_data = lidar.lidar('metoffice-lidar_faam_20150807_r0_B920_raw.nc')


# m_time = dates.epoch2num(lidar_data['Time'][:].data)
# full_altitude = lidar_data['Altitude (m)'][:].data
height_correction = 1.5 * np.arange(12148)

# using the mask option might avoid misrepresenting data, but it causes some warnings when using pcorlormesh
# the warnings don't seem to happen with pcorlor, not sure about contourf
def z_maker(x, y, channel = 0):
    data = lidar_data.profile[0][x:y].data.clip(0)
    data_m = ma.masked_invalid(data)
    return data_m
    # return np.nan_to_num(lidar_data.profile[channel][x:y].data.clip(0))

def height_maker(x, y, z):
    altitude = lidar_data['Altitude (m)'][x:y].data
    #altitude = full_altitude[x:y]
    altitude_array = np.empty_like(z)
    for j in range(0,len(z[0])):
        altitude_array[:,j] = altitude[j] - height_correction
    altitude_array = np.nan_to_num(altitude_array.clip(0))
    #altitude_array = altitude_array.clip(0)
    #height = ma.masked_invalid(altitude_array)
    return altitude_array

def time_maker(x, y, z):
    time = lidar_data['Time'][x:y].data
    time_array = np.empty_like(z)
    for j in range(0,len(z)):
        for i in range(0, len(z[j])):
            time_array[j,i] = time[i]
    mpl_time = dates.epoch2num(time_array)
    return mpl_time

def moment_maker(epoch_time):
    index = np.argwhere(lidar_data['Time'][:].data <= epoch_time).max()
    return index

def epoch_maker(date, time):
    time_dt = datetime.strptime(time, "%H:%M:%S").time()
    date_dt = datetime.strptime(date, "%d/%m/%Y")
    datetime_dt = datetime.combine(date_dt, time_dt)
    timestamp = datetime.timestamp(datetime_dt.replace(tzinfo=timezone.utc))
    return timestamp

def start_end_maker(start_string, end_string, date):
    start_e = epoch_maker(date, start_string)
    end_e = epoch_maker(date, end_string)
    start = moment_maker(start_e)
    end = moment_maker(end_e)
    return (start, end)

def time_type(s, pat=re.compile("([0-1]?\d|2[0-3]):([0-5]?\d):([0-5]?\d)")):
    if not pat.fullmatch(s):
        raise argparse.ArgumentTypeError("Please enter a valid time in the format HH:MM:SS.")
    return s

def date_type(s, pat=re.compile("^((([0-2]?\d|3[0-1])/(0?[1,3,5,7,8]|1[0,2]))"
                 "|(([0-2]?\d|30)/(0?[4,6,9]|11))"
                 "|(([0-2]?\d)/(0?2)))"
                 "/\d\d\d\d$")):
    if not pat.fullmatch(s):
        raise argparse.ArgumentTypeError("Please enter a valid date in the format DD/MM/YYYY.")
    return s

# def time_quick_maker(x,y,z):
#     time = m_time[x:y]
#     time_array = np.empty_like(z)
#     for j in range(0,len(z)):
#         for i in range(0, len(z[j])):
#             time_array[j,i] = time[i]
#     return time_array

# full_z = z_maker(0, len(lidar_data.profile[0][:].data[0]))
# full_height = height_maker(0, len(lidar_data.profile[0][:].data[0]), full_z)
# def height_quick_maker(x,y):
#     return full_height[:, x:y]

def plotter(start_time="14:13:33", end_time = "14:20:30", date = "7/8/2015", channel=0):
    # pcolor and pcolormesh could use time_tall
    (start, end) = start_end_maker(start_time, end_time, date)
    plt.gcf()
    # start = start_end[0]
    # end = start_end[1]
    if start > end:
        raise ValueError("and must be greate than start.")
    z = z_maker(start, end, channel)
    time = dates.epoch2num(lidar_data['Time'][start:end].data)
    #time_tall = time_maker(start, end, z)
    altitude = lidar_data['Altitude (m)'][start:end].data
    #altitude = full_altitude[start:end]
    height = height_maker(start, end, z)
    #height = height_quick_maker(start, end)
    if ~np.isnan(np.nanmax(altitude)):
        plt.ylim(0, np.nanmax(altitude) * 1.1)
    plt.ylabel('Height (m)')
    plt.xlabel('time')
    contour_p = plt.pcolormesh(time, height, z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))
    #contour_p = plt.pcolormesh(time_tall, height, z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))
    #contour_p = plt.pcolormesh(time, height,z, vmax=0.0007)
    #contour_p = plt.contourf(time_tall, height,z, locator=ticker.LogLocator())
    line_p = plt.plot(time, altitude, color='black', linewidth=2)
    myFmt = dates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    plt.colorbar(contour_p)

class Index(object):
    def next(self, event):
        print(ax.xaxis)
        print('start')
        #print(contour_p.get_array())
        plt.clf()
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




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Enter values for LIDAR processing.')
    # parser.add_argument('integers', metavar='start end', type=int, nargs='+',
    #                     help='an integer for the accumulator')
#    parser.add_argument('time', type=time_type)
    parser.add_argument('--start', type=time_type,
                        default="14:33:33", help='the start time in the format HH:MM:SS')
    parser.add_argument('--end', type=time_type,
                        default="14:53:33", help='the end time in the format HH:MM:SS')
    parser.add_argument('--date', type=date_type,
                        default="7/8/2015", help='the date time in the format DD/MM/YYYY')
    parser.add_argument('--plot', type=str, choices=['rock', 'paper', 'scissors'],
                        default='rock', help='which plot do you want')
    # parser.add_argument('--sum', dest='accumulate', action='store_const',
    #                     const=sum, default=max,
    #                     help='sum the integers (default: find the max)')

    # can't type python GUI.py end=15:03:33
    # would like to be able to specify variables based on name rather than order.

    # https://stackoverflow.com/questions/41881002/python-argparse-regex-expression
    # https://stackoverflow.com/questions/12595051/check-if-string-matches-pattern
    # https://docs.python.org/3/library/re.html

    args = parser.parse_args()
    # print(args.accumulate(args.integers))
    start = args.start
    end = args.end
    date = args.date
    plot = args.plot
    # time = args.time
    # print(time)

    try:
        start
    except NameError:
        start = None
    if start is None:
        print("Start not defined.")
    else:
        print(start)

    try:
        end
    except NameError:
        end = None
    if end is None:
        print("end not defined.")
    else:
        print(end)

    try:
        date
    except NameError:
        date = None
    if date is None:
        print("date not defined.")
    else:
        print(date)

    try:
        plot
    except NameError:
        plot = None
    if plot is None:
        print("plot not defined.")
    else:
        print(plot)

    print(start < end)

    # userInput = input("Would you like to start a new transaction?: ");
    # userInput = userInput.lower();
    #
    # #Validate input
    # while userInput in ['yes', 'no']:
    #     print ("Invalid input. Please try again.")
    #     userInput = input("Would you like to start a new transaction?: ")
    #     userInput = userInput.lower()

    # fig, ax = plt.subplots()
    # plt.subplots_adjust(bottom=0.2)
    #
    # plotter(start, end, date)
    #
    # callback = Index()
    # axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
    # axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    # bnext = Button(axnext, 'Next')
    # bnext.on_clicked(callback.next)
    # bprev = Button(axprev, 'Previous')
    # bprev.on_clicked(callback.prev)
    #
    # print("Near the end")
    # plt.show()