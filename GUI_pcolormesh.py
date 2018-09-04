import lidar
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib import colors, ticker, cm
from matplotlib import dates
import matplotlib

lidar_data=lidar.lidar('metoffice-lidar_faam_20150807_r0_B920_raw.nc')

m_time = dates.epoch2num(lidar_data['Time'][:].data)
full_altitude = lidar_data['Altitude (m)'][:].data
height_correction = 1.5 * np.arange(12148)

def z_maker(x,y):
    return lidar_data.profile[0][x:y].data

def height_maker(x,y,z):
    altitude = lidar_data['Altitude (m)'][x:y].data
    altitude_array = np.empty_like(z)
    for j in range(0,len(z[0])):
        altitude_array[:,j] = altitude[j] - height_correction
    altitude_array = altitude_array.clip(0)
    return altitude_array

def time_maker(x,y,z):
    time = lidar_data['Time'][x:y].data
    time_array = np.empty_like(z)
    for j in range(0,len(z)):
        for i in range(0, len(z[j])):
            time_array[j,i] = time[i]
    mpl_time = dates.epoch2num(time_array)
    return mpl_time

full_z = z_maker(0, len(lidar_data.profile[0][:].data[0]))

full_height = height_maker(0, len(lidar_data.profile[0][:].data[0]), full_z)

def height_quick_maker(x,y):
    return full_height[:, x:y]

fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)
start = 2000
end = 2200
z = z_maker(start, end)
time = m_time[start:end]
altitude = full_altitude[start:end]
height = height_quick_maker(start, end)
plt.ylim(0, altitude.max() * 1.1)
plt.ylabel('Height (m)')
plt.xlabel('time')
c = plt.pcolormesh(time,height,z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))
d = plt.plot(time, altitude, color='black', linewidth=2)
myFmt = dates.DateFormatter('%H:%M')
ax.xaxis.set_major_formatter(myFmt)
plt.colorbar(c)

# fig, ax = plt.subplots()
# plt.subplots_adjust(bottom=0.2)
# start = 2000
# end = 2200
# z = z_maker(start, end)
# time = time_maker(start, end, z)
# time_flat = m_time[start:end]
# altitude = full_altitude[start:end]
# height = height_quick_maker(start, end)
# plt.ylim(0, altitude.max() * 1.1)
# plt.ylabel('Height (m)')
# plt.xlabel('time')
# c = plt.pcolormesh(time,height,z, norm=colors.LogNorm(vmin=0.000001, vmax=z.max()))
# d = plt.plot(time_flat, altitude, color='black', linewidth=2)
# myFmt = dates.DateFormatter('%H:%M')
# ax.xaxis.set_major_formatter(myFmt)
# plt.colorbar(c)

# fig, ax = plt.subplots()
# plt.subplots_adjust(bottom=0.2)
# start = 2000
# end = 2200
# z = z_maker(start, end)
# time = m_time[start:end]
# altitude = full_altitude[start:end]
# height = height_quick_maker(start, end)
# plt.ylim(0, altitude.max() * 1.1)
# plt.ylabel('Height (m)')
# plt.xlabel('time')
# contour_p = plt.pcolormesh(time,height,z, vmax=0.0007)
# line_p = plt.plot(time, altitude, color='black', linewidth=2)
# myFmt = dates.DateFormatter('%H:%M')
# ax.xaxis.set_major_formatter(myFmt)
# plt.colorbar(contour_p)

class Index(object):
    def next(self, event):
        print(start)
        print(c.get_array())
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

callback = Index()
axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
bnext = Button(axnext, 'Next')
bnext.on_clicked(callback.next)
bprev = Button(axprev, 'Previous')
bprev.on_clicked(callback.prev)

print("Near the end")
plt.show()