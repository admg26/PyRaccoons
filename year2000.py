from __future__ import print_function
from rad_params import LW 
import pygeode as pyg
import numpy as np
from pygeode.atmdyn import constants as c

#def main():
dir_path = "/data/apollon/atmos/data/ECMWF/incoming/"
## Read in specific humidity and convert into vmr
#q = pyg.open(dir_path + 'EI_HR_analysis2000123000.nc', varlist = ['q'])
#q = q / (1-q) * (28.966 / 18.016)

# Read in ozone from Fortuin and Kelder climatology
fko3 = np.loadtxt('/data/athena/adk33/ERA_interim/fortuin_kelder_o3mean.dat',comments='Month')
fko3 = fko3.reshape((12,19,17)) * 1e-6
lato3 = pyg.Lat(range(-80,90,10))
po3 = pyg.Pres([1000, 700, 500, 300, 200, 150, 100, 70, 50, 30, 20, 10, 7, 5, 3, 2, 1, 0.5, 0.3])
t_3yrs = pyg.StandardTime(units='days', values=np.arange(365*3), startdate=dict(year=1999, month=1, day=1))

t = t_3yrs(year = 2000)
to3 = t_3yrs(day = 15)

o3_mon = pyg.Var((to3, po3, lato3), name='o3_mon',values=np.concatenate((fko3,fko3,fko3),axis=0),\
              atts={'Units': 'vmr in ppmv'})
o3_3yrs = o3_mon.interpolate(to3, t_3yrs, interp_type='cspline')
o3 = o3_3yrs(year = 2000)
o3.name = 'o3'

# Load A and B values for model levels
mlpath = '/data/apollon/atmos/data/ECMWF/ERA_INTERIM/instant/model_lev/2000/'
A = np.loadtxt('full_ab.txt', usecols=(1,))
B = np.loadtxt('full_ab.txt', usecols=(2,))

# Set hybrid values appropriate for a reference surface pressure
p0 = 101325
mldt = dict(level =  pyg.Hybrid(A/p0 + B, A=A, B=B))
mlp = pyg.Pres(mldt['level'](eta=(0.3 * 100 / p0, 1))[:] * p0 / 100)

# Names of tendency variables
nm = {'p100.162':'qtendASSW', \
      'p101.162':'qtendASLW', \
      'p102.162':'qtendCSSW', \
      'p103.162':'qtendCSLW', \
      'p110.162':'Ttend'}

# Read in data sets
pattern = '$Y$m$d$H.nc'
mlan = pyg.open_multi(mlpath + 'EI_HR_analysis2000*.nc', pattern=pattern, \
             dimtypes=mldt)
mlsfc = pyg.open_multi(mlpath + 'EI_HR_sfcforecast2000*.nc', pattern=pattern)
mlfc = pyg.open_multi(mlpath + 'EI_HR_forecast2000*.nc', pattern=pattern, \
                 dimtypes=mldt, namemap=nm)

#convert h2o specific humidity to volume mixing ratio
h2o = mlan.q.mean(pyg.Lon) / (1 - mlan.q.mean(pyg.Lon)) * (28.966 / 18.016)
h2o.name = 'h2o'

#pick out one latitude and make daily averages 
lat = 0.0
time = 0

Tm = pyg.dailymean(mlan.t(latitude = lat, eta = (0.3 * 100 / p0, 1)).mean(pyg.Lon))
h2om = pyg.dailymean(h2o(latitude = lat, eta = (0.3 * 100 / p0, 1)))
SSTm = pyg.dailymean(mlsfc.skt(latitude = lat).mean(pyg.Lon))
SPm = pyg.dailymean(mlan.lnsp(latitude = lat, eta = 0).mean(pyg.Lon)).exp()

#Interpolate o3 to hybrid levels
o3m = o3(lat = lat).interpolate(po3, mlp, interp_type='cspline').fill(0.0)

nlayers = 60 # not used
nlevels = len(mlp)

LW_erai = LW('lw', NLEV = nlevels, NLAY = nlayers)

# Record 1.2
LW_erai.IATM = 1
LW_erai.IXSECT = 0
LW_erai.NUMANGS = 4
LW_erai.IOUT = 0
LW_erai.NUMANGS = 4
LW_erai.ICLD = 0
 
# Record 1.4  
LW_erai.TBOUND = SSTm(i_time = 0)[:].flatten()[0]
LW_erai.IEMIS = 1
LW_erai.SEMISS= 0.6

# Record 1.4  
LW_erai.MODEL = 0
LW_erai.IBMAX = 0
LW_erai.NMOL = 7
LW_erai.CO2MX = 0
LW_erai.REF_LAT = lat

# Record 3.2
#convert to hPa
LW_erai.HBOUND = SPm(i_time = 0)[:].flatten()[0] / 100 
LW_erai.HTOA = mldt['level'][0] * p0 / 100 

## Record 3.3B2
#LW_erai.PBND =  

# Record 3.4
LW_erai.IMMAX = -nlevels

# Record 3.5
# Only the first z level matters
zlevels = np.zeros(nlevels)
zlevels[0] = 10

LW_erai.ZM = zlevels 
LW_erai.PM = np.flipud(mldt['level']) * p0 / 100
LW_erai.TM = Tm(time = 0)[:].flatten()  
LW_erai.JCHARP = 'A'
LW_erai.JCHART = 'A'
LW_erai.JCHAR = 'AAA6666'

# Record 3.6
co2 = np.empty(nlevels) 
co2.fill(370e-6)

LW_erai.VMOLH2O = h2om(i_time = 0)[:].flatten()
LW_erai.VMOLO3 = o3m(i_time = 0)[:].flatten()
LW_erai.VMOLCO2 = co2

f = open('INPUT_RRTM', 'w')
print('$', file = f)
print(LW_erai.write(), file = f)
print('%', file = f)
f.close()
#

#if __name__ == "__main__":
#    main()
