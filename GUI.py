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


lidar_data = lidar.lidar('metoffice-lidar_faam_20150807_r0_B920_raw.nc')
time_0 = lidar_data['Time'][0]
date = datetime.utcfromtimestamp(time_0.item())
start_moment = 200
end_moment = 400
PLOT_OPTIONS =  {'LINEAR', 'CONTOURF', 'PCOLOR', 'PCOLORMESH'}
VALID_CHANNELS = {0, 1, 2}

# m_time = dates.epoch2num(lidar_data['Time'][:].data)
# full_altitude = lidar_data['Altitude (m)'][:].data
height_correction = 1.5 * np.arange(12148)

# using the mask option might avoid misrepresenting data, but it causes some warnings when using pcorlormesh
# the warnings don't seem to happen with pcorlor, not sure about contourf
def z_maker(x, y, channel = 0):
    data = lidar_data.profile[channel][x:y].data.clip(0)
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
    time_array = lidar_data['Time'][:].data
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

def epoch_maker(time_string):
    time_dt = datetime.strptime(time_string, "%H:%M:%S").time()
    #
    datetime_dt = datetime.combine(date, time_dt)
    timestamp = datetime.timestamp(datetime_dt.replace(tzinfo=timezone.utc))
    return timestamp

def start_end_maker(start_string, end_string):
    start_e = epoch_maker(start_string)
    end_e = epoch_maker(end_string)
    print("Start is " + str(start_e))
    print("End is " + str(end_e))
    start = moment_maker(start_e)
    end = moment_maker(end_e)
    return (start, end)

def time_type(s):
    pat = re.compile("([0-1]?\d|2[0-3]):([0-5]?\d):([0-5]?\d)")
    if not pat.fullmatch(s):
        raise argparse.ArgumentTypeError("Please enter a valid time in the format HH:MM:SS.")
    return s

def date_type(s):
    pat = re.compile("^((([0-2]?\d|3[0-1])/(0?[1,3,5,7,8]|1[0,2]))"
                     "|(([0-2]?\d|30)/(0?[4,6,9]|11))"
                     "|(([0-2]?\d)/(0?2)))"
                     "/\d\d\d\d$")
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

#contour and contourf are slow and contour leaves white space
#pcolor is slow
def plotter(start_time="14:13:33", end_time = "14:20:30", channel=0, plot_choice="PCOLORMESH"):
    if plot_choice not in PLOT_OPTIONS:
        raise ValueError("plot_choice must be one of {}.".format(PLOT_OPTIONS))
    if channel not in VALID_CHANNELS:
        raise ValueError("channel must be one of {}.".format(PLOT_OPTIONS))
    # pcolor and pcolormesh could use time_tall
    (start, end) = start_end_maker(start_time, end_time)
    # start = start_end[0]
    # end = start_end[1]
    length = lidar_data['Time'][:].data.shape[0]
    # make sure it's modulo the right value
    # ask on stack overflow if there's a more effecient way of doing this
    if start % length >= end % length:
        raise ValueError("End must be greater than start.")
    plt.gcf()
    z = z_maker(start, end, channel)
    time = dates.epoch2num(lidar_data['Time'][start:end].data)
    altitude = lidar_data['Altitude (m)'][start:end].data
    #altitude = full_altitude[start:end]
    height = height_maker(start, end, z)
    #height = height_quick_maker(start, end)
    if ~np.isnan(np.nanmax(altitude)):
        plt.ylim(0, np.nanmax(altitude) * 1.1)
    plt.ylabel('Height (m)')
    plt.xlabel('time')
    print(plot_choice)
    if plot_choice == "PCOLOR":
        print("It is pcolor")
        contour_p = plt.pcolor(time, height, z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))
    elif plot_choice == "LINEAR":
        print("It is linear")
        contour_p = plt.pcolormesh(time, height, z, vmax=0.0007)
    elif plot_choice == "CONTOURF":
        print("It is contourf")
        time_tall = time_maker(start, end, z)
        contour_p = plt.contourf(time_tall, height, z, locator=ticker.LogLocator())
    else:
        print("It is log")
        contour_p = plt.pcolormesh(time, height, z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))
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
    parser = argparse.ArgumentParser(description='Enter values for LIDAR processing.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # parser.add_argument('integers', metavar='start end', type=int, nargs='+',
    #                     help='an integer for the accumulator')
#    parser.add_argument('time', type=time_type)
    parser.add_argument('--start', type=time_type,
                        default="14:33:33", help='the start time in the format HH:MM:SS')
    parser.add_argument('--end', type=time_type,
                        default="14:53:33", help='the end time in the format HH:MM:SS')
    parser.add_argument('--date', type=date_type,
                        default=None, help='the date time in the format DD/MM/YYYY')
    parser.add_argument('--plot_choice', type=str, choices=PLOT_OPTIONS,
                        default='PCOLORMESH', help='Which plot do you want')
    parser.add_argument('--channel', type=int, choices=VALID_CHANNELS,
                        default=0, help='Which LIDAR channel do you want data from?')
    parser.add_argument('--file_path', type=str, default='metoffice-lidar_faam_20150807_r0_B920_raw.nc',
                        help='Enter the path to the NetCDF file containing the LIDAAR data.')
    # parser.add_argument('--sum', dest='accumulate', action='store_const',
    #                     const=sum, default=max,
    #                     help='sum the integers (default: find the max)')




    args = parser.parse_args()
    file_path = args.file_path
    lidar_data = lidar.lidar(file_path)
    date_string = args.date

    if date_string == None:
        print("String was none")
        time_0 = lidar_data['Time'][0]
        date = datetime.utcfromtimestamp(time_0.item())
    else:
        date = datetime.strptime(date_string, "%d/%m/%Y")
        print("String was not none.")

    start_string = args.start
    if start_string == None:
        print("start String was none")
        start_epoch = lidar_data['Time'][0]
        start_moment = moment_maker(start_epoch)
    else:
        start_epoch = epoch_maker(start_string)
        start_moment = moment_maker(start_epoch)
        print("start String was not none.")

    # print(args.accumulate(args.integers))

    end = args.end

    plot_choice = args.plot_choice
    channel = args.channel
    print(6+channel)
    # time = args.time
    # print(time)


    print(start_string)
    print(end)
    print(date)
    print(plot_choice)

    print(start_string < end)

    if end < start_string:
        raise ValueError("Start must come before end.")

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.2)

    plotter(start_string, end, channel=channel, plot_choice=plot_choice)

    callback = Index()
    axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
    axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    bnext = Button(axnext, 'Next')
    bnext.on_clicked(callback.next)
    bprev = Button(axprev, 'Previous')
    bprev.on_clicked(callback.prev)

    print("Near the end")
    plt.show()