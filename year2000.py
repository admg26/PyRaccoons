from __future__ import print_function
from rad_params import LW 
import pygeode as pyg
import numpy as np
from pygeode.atmdyn import constants as c
import matplotlib.pyplot as plt

import os
import sys
import shutil
import subprocess
import re

#def main():
dir_path = "/data/apollon/atmos/data/ECMWF/incoming/"
## Read in specific humidity and convert into vmr
#q = pyg.open(dir_path + 'EI_HR_analysis2000123000.nc', varlist = ['q'])
#q = q / (1-q) * (28.966 / 18.016)

# Read in ozone from Fortuin and Kelder climatology
fko3 = np.loadtxt('/data/athena/adk33/ERA_interim/fortuin_kelder_o3mean.dat',comments='Month')
fko3 = fko3.reshape((12,19,17)) * 1e-6 
lato3 = pyg.Lat(range(-80,90,10))
ptmp = np.array([1000, 700, 500, 300, 200, 150, 100, 70, 50, 30, 20, 10, 7, 5, 3, 2, 1, 0.5, 0.3])
po3 = pyg.Pres(ptmp)
#po3 = pyg.Pres([1000, 700, 500, 300, 200, 150, 100, 70, 50, 30, 20, 10, 7, 5, 3, 2, 1, 0.5, 0.3])

t_3yrs = pyg.StandardTime(units='days', values=np.arange(365*3), startdate=dict(year=1999, month=1, day=1))

t = t_3yrs(year = 2000)
to3 = t_3yrs(day = 15)

o3_mon = pyg.Var((to3, po3, lato3), name='o3_mon',values=np.concatenate((fko3,fko3,fko3),axis=0),\
              atts={'Units': 'vmr in ppmv'})
o3_3yrs = o3_mon.interpolate(to3, t_3yrs, interp_type='linear')
o3 = o3_3yrs(year = 2000)
o3.name = 'o3'

# Load A and B values for model levels
mlpath = '/data/apollon/atmos/data/ECMWF/ERA_INTERIM/instant/model_lev/2000/'
#A = np.loadtxt('full_ab.txt', usecols=(1,))
#B = np.loadtxt('full_ab.txt', usecols=(2,))
A = np.loadtxt('half_ab.txt', usecols=(1,))
B = np.loadtxt('half_ab.txt', usecols=(2,))

## Set hybrid values appropriate for a reference surface pressure
#p0 = 10i1325
#mldt = dict(level =  pyg.Hybrid(A/p0 + B, A=A, B=B))
#mlp = pyg.Pres(mldt['level'][:] * p0 / 100)


# Names of tendency variables
nmq = {'p100.162':'qtendASSW', \
      'p101.162':'qtendASLW', \
      'p102.162':'qtendCSSW', \
      'p103.162':'qtendCSLW', \
      'p110.162':'Ttend'}

nmlatlon = {'latitude':'lat', 'longitude':'lon'}

# Read in data sets
pattern = '$Y$m$d$H.nc'
mlan = pyg.open_multi(mlpath + 'EI_HR_analysis2000*.nc', pattern=pattern, namemap = nmlatlon)
mlsfc = pyg.open_multi(mlpath + 'EI_HR_sfcforecast2000*.nc', pattern=pattern, namemap = nmlatlon)
mlfc = pyg.open_multi(mlpath + 'EI_HR_forecast2000*.nc', pattern=pattern,namemap=nmq)

mlan.name = 'o3'
surfgeo =  pyg.open('/data/athena/atmos/era_interim/erai_surfacegeo.nc', namemap = nmlatlon)

#convert h2o specific humidity to volume mixing ratio
#h2o = mlan.q.mean(pyg.Lon) / (1 - mlan.q.mean(pyg.Lon)) * (28.966 / 18.016) 
#h2o = mlan.q(lon = 0) / (1 - mlan.q(lon = 0)) * (28.966 / 18.016) 
h2o = mlan.q / (1 - mlan.q) * (28.966 / 18.016) 
h2o.name = 'h2o'


##pick out one latitude and make daily averages 
#lat = 0.0
#time = 0
Tm = pyg.dailymean(mlan.t)
h2om = pyg.dailymean(h2o)
o3m = pyg.dailymean(o3)
SSTm = pyg.dailymean(mlsfc.skt)
SPm = pyg.dailymean(mlan.lnsp(i_level = 0)).squeeze().exp()
zg1 = surfgeo.z / c.g0
zg = zg1.interpolate(zg1.Lon, SPm.Lon, interp_type='linear')


#Tm = mlan.t(time= '00:00 10 jan 2000')
#h2om = h2o(time= '00:00 10 jan 2000')
#o3m = o3(time= '00:00 10 jan 2000')
#SSTm = mlsfc.skt(time= '00:00 10 jan 2000')
#SPm_tmp = mlan.lnsp(level = 1).squeeze().exp()
#SPm = SPm_tmp(time= '00:00 10 jan 2000')
#zg = surfgeo.z / c.g0

#Tm = pyg.dailymean(mlan.t)
#h2om = pyg.dailymean(h2o)
#SSTm = pyg.dailymean(mlsfc.skt)
#SPm = pyg.dailymean(mlan.lnsp(i_level = 0)).exp().squeeze()
#zg = surfgeo.z / c.g0

nlayers = 60
nlevels = 60 + 1

LW_erai = LW('lw', NLEV = nlevels, NLAY = nlayers)

# Record 1.2
LW_erai.IATM = 1
LW_erai.IXSECT = 0
LW_erai.NUMANGS = 4
LW_erai.IOUT = 0
LW_erai.ICLD = 0
 
# Record 1.4  
LW_erai.IEMIS = 2
emis = np.ones(16)
emis[:5] = 0.99
emis[5:8] = 0.99
emis[8:] = 0.99
LW_erai.SEMISS = emis

# Record 3.1  
LW_erai.MODEL = 0
LW_erai.IBMAX = -nlayers
LW_erai.NOPRNT = 0
LW_erai.NMOL = 7
LW_erai.CO2MX = 0

# Record 3.6
LW_erai.JCHARP = 'A'
LW_erai.JCHART = 'A'
LW_erai.JCHAR = 'AAAAAAA'

latval = np.arange(-40,45,5)
lonval = np.arange(-180,180,30)
lat_sh = pyg.Lat(latval)
lon_sh = pyg.Lon(lonval)

level_hf = pyg.NamedAxis(np.arange(0.5,61,1),name='level')
A1 = pyg.Var((SPm.time, lat_sh, lon_sh, level_hf),name='A', values = np.tile(A,(len(SPm.time), len(lat_sh), len(lon_sh), 1)))
B1 = pyg.Var((SPm.time, lat_sh, lon_sh, level_hf),name='B', values = np.tile(B,(len(SPm.time), len(lat_sh), len(lon_sh), 1)))

SP = SPm.extend(3, A1.level).sorted('lat')

# p_half = A + B* p_surface. Gives values in hPa
p_half =  (A1 + B1 * SP(l_lat = latval, l_lon = lonval)) / 100.0 

pf1 = p_half.interpolate(p_half.level, Tm.level, interp_type = 'linear')

SP_tmp = SPm(l_lat = latval, l_lon = lonval).extend(3, pyg.NamedAxis(np.arange(61,62,1),name = 'level'))
SP_tmp = SP_tmp.sorted('lat')
pf2 = pyg.concat.concat([SP_tmp / 100.0, pf1])
pf3 = pf2.sorted('level')
p_full = pf3.replace_axes(time = o3m.time)

o3lat = o3m.interpolate(lato3, lat_sh, interp_type='linear', d_below = 0, d_above = 0)
o3_tmp = o3lat.extend(3, lon_sh)
o3m = o3_tmp.interpolate(o3_tmp.pres, p_full.level, outx = p_full, interp_type = 'linear', d_below = 0, d_above = 0)

SSTm_f = SSTm(l_lat = latval, l_lon = lonval)[:]
zg_f = zg(l_lat = latval, l_lon = lonval).squeeze()[:] 
o3m_f = o3m(l_lat = latval, l_lon = lonval)[:] 
h2om_f1 = h2om(l_lat = latval, l_lon = lonval)[:]
h2om_f = np.transpose(h2om_f1, (0,2,3,1))

p_full_f = p_full(l_lat = lat_latval, l_lon = lonval)[:] 
p_half_f = p_half(l_lat = lat_latval, l_lon = lonval)[:] 
Tm_f1 = Tm(l_lat = lat_latval, l_lon = lonval)[:] 
Tm_f = np.transpose(Tm_f1, (0,2,3,1))

for ilat, lat in enumerate(latval):
  print(lat) 
  for itime in range(366):
    for ilon, lon in enumerate(lonval):
    #for ilon, lon in enumerate([0]):
  
    # Record 1.4  
      LW_erai.TBOUND = Tm_f[itime, ilat, ilon, :] 
    
      #layers = p_half(lat = lat, lon = lon, i_time = itime)[:].flatten()[::-1]
      layers = p_half_f[itime, ilat, ilon, :][::-1]
  
      # Record 3.1  
      LW_erai.IBMAX = -nlayers
      LW_erai.REF_LAT = float(lat)
    
      # Record 3.2
      #convert to hPa
      #LW_erai.HBOUND = SPm(i_time = 0)[:].flatten()[0] / 100 
      
      LW_erai.HBOUND = p_full(level = 61, lat = lat, lon = lon, i_time = itime)[:].flatten()[0]  #0.0 
      LW_erai.HTOA = p_full(level = 1, lat = lat, lon = lon, i_time = itime)[:].flatten()[0]    #54.0
      
      ## Record 3.3B2
      LW_erai.PBND = layers 
      
      # Record 3.1
      LW_erai.IMMAX = -nlevels
      
      # Record 3.5
      # Only the first z level matters
      zlevels = np.zeros(nlevels)
      # surface geopotential height in km
      #zlevels[0] = max(0.0, zg(lat = lat, lon = lon)[:].flatten()[0] / 1.0e3)
      zlevels[0] = max(0.0, zg_f[itime, ilat, ilon] / 1.0e3)
    
      # Record 3.5
      LW_erai.ZM = zlevels 
      #LW_erai.PM = p_full(lat = lat, lon = lon, i_time = itime)[:].flatten()[::-1]  
      LW_erai.PM = p_full_f[itime, ilat, ilon, :][::-1]  
      #T_tmp = Tm(lat = lat, lon = lon, i_time = itime)[:].flatten()
      T_tmp = Tm_f[itime, ilat, ilon, :]
      LW_erai.TM = np.append(T_tmp, LW_erai.TBOUND)[::-1]
    
      # Record 3.6
      co2 = np.empty(nlevels) 
      co2.fill(370e-6)
      n2o = np.empty(nlevels) 
      n2o.fill(316e-9)
      ch4 = np.empty(nlevels) 
      ch4.fill(1780e-9)
    
      #reverse arrays since first element of VMOL is closest to the ground
      #h2o_tmp = h2om(lat = lat, lon = lon, i_time = itime)[:].flatten() * 1.0e6
      h2o_tmp = h2om_f[itime, ilat, ilon, :] * 1.0e6
  
      LW_erai.VMOLH2O = np.append(h2o_tmp, h2o_tmp[-1])[::-1]
      #LW_erai.VMOLO3 = o3m(lat = lat, lon = lon, i_time = itime)[:].flatten()[::-1] * 1.0e6
      o3_tmp1 = o3m[itime, ilat, ilon, :] * 1.0e6
      LW_erai.VMOLO3 = o3m_tmp1[::-1] 
      LW_erai.VMOLCO2 = co2 * 1.0e6
      LW_erai.VMOLN2O = n2o * 1.0e6
      LW_erai.VMOLCH4 = ch4 * 1.0e6
    
      filename = 'control_' + str(ilat + 1) + '_' +  str(ilon + 1) + '_' + str(itime + 1) + '.dat' 
    
      f = open('input_files/' + filename, 'w')
      print('$', file = f)
      print(LW_erai.write(), file = f)
      print('%', file = f)
      f.close()


# mv file to INPUT_RRTM and call RRTM
currentdir = os.path.dirname(os.path.realpath(__file__))
regex = re.compile(r'\d+')
filepath_out = os.path.join(currentdir,'output_files')

for subdirs, dirs, files in os.walk(os.path.join(currentdir,'input_files')):
    files = [f for f in files if not f[0] == '.']
    for file in files:
        filepath_in = os.path.join(subdirs,file)
        shutil.copy(filepath_in,currentdir)
        os.rename(file,'INPUT_RRTM')
        print(file)

        #run rrtm_lw
        subprocess.call("rrtm_v3.3_linux_ifort")
        file_ind = regex.findall(file)
        output_file ='lw_'+ file_ind[0] + '_' + file_ind[1] + '_' + file_ind[2] +  '.dat' 
        os.rename('OUTPUT_RRTM',output_file)
        shutil.move(output_file,filepath_out)

##read in output file OUTPUT_RRTM
#q_lw = np.genfromtxt("OUTPUT_RRTM", skip_header=3, skip_footer=18, usecols=(5)) 
#p1 = np.genfromtxt("OUTPUT_RRTM", skip_header=3, skip_footer=18, usecols=(1)) 
#
#qtend1 = mlfc.qtendCSLW(lat = lat, lon = lon).squeeze()
#qerai = (qtend1(time= '06:00 10 jan 2000').squeeze()[:]) * 4.0
##qerai = (qtend1(time= '18:00 1 jan 2000').squeeze()[:]) * 4.0
#
#
#plt.figure(6)
#plt.clf
#plt1 = plt.semilogy(q_lw,p1)
#plt2 = plt.semilogy(qerai, p_full(lat = lat, lon = lon, i_time = itime)[:].flatten()[:-1], linestyle='dashed')
#plt.legend([plt1[0],plt2[0]],['rrtm lw','Q era lw'])
#
#ax = plt.gca()
#ax.invert_yaxis()
#ax.set_xlabel('Q (K day$^{-1}$)')
#ax.set_ylabel('p (hPa)')
#ax.set_title('Q lw at lat = ' + str(lat) + ' and lon = ' + str(lon))
#
#yticks = np.array([0.1, 0.3, 1, 5, 10, 20, 50, 100, 200, 500, 1000])
#ylabels = []
#for i in yticks:
#  ylabels.append(str(i))
#
#plt.yticks(yticks,ylabels)
#
#plt.show()

#if __name__ == "__main__":
#    main()
