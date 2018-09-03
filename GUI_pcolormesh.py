import lidar
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from matplotlib.widgets import Button
import matplotlib
import matplotlib.tri as mtri
from datetime import datetime, timedelta

lidar_data=lidar.lidar('metoffice-lidar_faam_20150807_r0_B920_raw.nc')




time_epoch = lidar_data['Time'][:].data
epoch_list = time_epoch.tolist()
datetime_list = [datetime.utcfromtimestamp(epoch_list[i]) for i in range(0, len(epoch_list))]
datetime_array = np.array(datetime_list)

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



full_z = z_maker(0, len(lidar_data.profile[0][:].data[0]))

full_height = height_maker(0, len(lidar_data.profile[0][:].data[0]), full_z)

def height_quick_maker(x,y):
    return full_height[:, x:y]




fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.2)

start = 2000
end = 2200
z_test = z_maker(start, end)
time_test = datetime_array[start:end]
# time_base = datetime_array[start:end]
# base_list = time_base.tolist()
height_test = height_quick_maker(start, end)
width = end - start
c = plt.pcolormesh(time_test,height_test,z_test, norm=colors.LogNorm(vmin=0.000001, vmax=z_test.max()))
print(z_test.max())
plt.colorbar(c)



class Index(object):
    start = 2000
    end = 2200

    def next(self, event):
        start = 2000
        end = 2200
        start += 100
        end += 100
        z_test = z_maker(start, end)
        time_test = datetime_array[start:end]
        height_test = height_quick_maker(start, end)
        c = plt.pcolormesh(time_test,height_test,z_test, norm=colors.LogNorm(vmin=0.000001, vmax=z_test.max()))
        plt.colorbar(c)
        plt.draw()

    def prev(self, event):
        print("pooop")



callback = Index()
axprev = plt.axes([0.7, 0.05, 0.1, 0.075])
axnext = plt.axes([0.81, 0.05, 0.1, 0.075])
bnext = Button(axnext, 'Next')
bnext.on_clicked(callback.next)
bprev = Button(axprev, 'Previous')
bprev.on_clicked(callback.prev)





plt.show()