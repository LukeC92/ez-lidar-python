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
import argparse


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

def plotter(start=2000, end=2200, channel=0):
    # pcolor and pcolormesh could use time_tall
    plt.gcf()
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



parser = argparse.ArgumentParser(description='Process some integers.')
# parser.add_argument('integers', metavar='start end', type=int, nargs='+',
#                     help='an integer for the accumulator')
parser.add_argument('start', metavar='start', type=int, nargs='?',
                    default=None, help='the start moment')
parser.add_argument('--sum', dest='accumulate', action='store_const',
                    const=sum, default=max,
                    help='sum the integers (default: find the max)')

args = parser.parse_args()
#print(args.accumulate(args.integers))
start = args.start

try:
    start
except NameError:
    start = None

if start is None:
    print("Start not defined.")
else:
    print(start)

if __name__ == '__main__':
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.2)

    plotter(start, 600)

    callback = Index()
    axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
    axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
    bnext = Button(axnext, 'Next')
    bnext.on_clicked(callback.next)
    bprev = Button(axprev, 'Previous')
    bprev.on_clicked(callback.prev)

    print("Near the end")
    plt.show()