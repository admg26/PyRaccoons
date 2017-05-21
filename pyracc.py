from params import Param, Namelist, ParamSet
import numpy as np

def lw(prmname, Nl, Np = 1, **kwargs):
# {{{
    return lwprms[prmname](Nl, Np, **kwargs)
# }}}

def sw(prmname, Nl, Np = 1, **kwargs):
# {{{
    return swprms[prmname](Nl, Np, **kwargs)
# }}}

def listcodes():
# {{{
    print 'Longwave: '
    for k in lwprms.keys():
        print k

    print 'Shortwave: '
    for k in swprms.keys():
        print k
# }}}

import pyr_rrtmg
import pyr_rrtm

lwprms = dict(RRTMG = pyr_rrtmg.RRTMG_LW,
              RRTM  = pyr_rrtm.RRTM_LW)
swprms = dict(RRTMG = pyr_rrtmg.RRTMG_SW,
              RRTM  = pyr_rrtm.RRTM_SW)

Nl = 80
zh = np.linspace(60, 0, Nl+1)
ph = 1000.*np.exp(-zh / 7.)
pf = np.sqrt(ph[:-1] * ph[1:]) 

prm1 = lw('RRTMG', Nl, 1, pres=pf, phalf=ph)
prm2 = sw('RRTMG', Nl, 1, pres=pf, phalf=ph)
prm3 = lw('RRTM', Nl, 1, pres=pf, phalf=ph)
# Example usage
#   import pyraccoons as pyr

#   # Construct longwave object; specify parameterization, optionally arguments
#   LW = pyr.lw('RRTM')  # number of profiles? 

#   # Set parameters for profile
#   LW.set(emis = 0.99)
#   LW.settracer('ppmv', CO2 = 360., O3 = o3prof, H2O = h2oprof)
#   LW.setprofile(pres = pf, temp = t, tsfc = t0)
#   res = LW.run()

#   res = pyg.runlw('RRTM', pres=pres, temp=temp, 
