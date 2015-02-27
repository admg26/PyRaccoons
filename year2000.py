from __future__ import print_function
from rad_params import LW 
import pygeode as pyg
import numpy as np
from  pygeode.formats import netcdf as nc
from pygeode.atmdyn import constants as c

def main():
    dir_path = "/data/apollon/atmos/data/ECMWF/incoming/"
    # Read in specific humidity and convert into vmr
    q = pyg.open(dir_path + 'EI_HR_analysis2000123000.nc', format = nc, varlist = ['q'])
    q = q / (1-q) * (28.966 / 18.016)

    # Read in ozone from Fortuin and Kelder climatology
    fko3 = np.loadtxt('/data/athena/adk33/ERA_interim/fortuin_kelder_o3mean.dat',comments='Month')
    fko3 = fko3.reshape((19,12,17)) * 1e-6
    lato3 = pyg.Lat(range(-80,90,10))
    po3 = pyg.Pres([1000, 700, 500, 300, 200, 150, 100, 70, 50, 30, 20, 10, 7, 5, 3, 2, 1, 0.5, 0.3])
    to3 = pyg.TAxis(range(1,13))
    o3 = pyg.Var((t,pres,lat), name='o3',values=fko3, atts={'Units': 'vmr in ppmv'})

    # Read in T profile, surface geopotential and surface T
    T = pyg.open(dir_path + '??.nc', format = nc, varlist = ['t'])
    z_surf = pyg.open(dir_path + '??.nc', format = nc, varlist = ['z'])
    z_surf.z = phi_surf.z / c.g0
    T_surf = pyg.open(dir_path + '??.nc', format = nc, varlist = ['sst'])

    nlevels = 100
    nlayers = 60
    lat = q.latitude[80]
    time = q.time[80]
    LW_erai = LW('lw', NLEV = nlevels, NLAY = nlayers)

    # Record 1.2
    LW_erai.IATM = 0
    LW_erai.IXSECT = 0
    LW_erai.NUMANGS = 4
    LW_erai.IOUT = 0
    LW_erai.NUMANGS = 4
    LW_erai.ICLD = 0
     
    # Record 1.4  
    LW_erai.TBOUND = T_surf.sst.mean('lon',pyg.Lon)(lat= , t= )

    f = open('INPUT_RRTM', 'w')
    print('$', file = f)
    print(TestLW.write(), file = f)
    print('%', file = f)
    f.close()


if __name__ == "__main__":
    main()
