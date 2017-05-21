import numpy as np
import params
from rrtm import rrtmg

class RRTMG_LW(params.LW):
# {{{
    prmname = 'RRTMG'

    # Define parameter model, serialization options
    def __init__(self, Nl, Np=1, **kwargs):
    # {{{
        lists = []
        params.LW.__init__(self, self.prmname, Nl, Np, lists=lists, **kwargs)
    # }}}

    def run(self):
    # {{{
        def sanitize(a): return np.asfortranarray(a[:], 'd')

        t    = sanitize(self.T)
        pf   = sanitize(self.pres)
        ph   = sanitize(self.phalf)

        co2  = sanitize(self.CO2)
        h2o  = sanitize(self.H2O)
        o3   = sanitize(self.O3)

        tsfc = sanitize(self.Tsfc)
        emis = sanitize(self.emis)

        if np.any(np.diff(pf)) < 0. or np.any(np.diff(ph) < 0.):
            raise ValueError('Pressure values must be strictly increasing.')

        for chi, name in zip([co2, h2o, o3], ['CO2', 'H2O', 'O3']):
            if np.any(chi < 0.) or np.any(np.isnan(chi)):
                raise ValueError('%s values must be finite and non-negative.' % name)

        rrtmg.init(self.cpair)

        retv = rrtmg.rrtmg_lw(pf, ph, t, tsfc, emis, co2, h2o, o3)

        rd = self._lwout()
        rd.lwhr   = retv['lwhr']
        rd.uflxlw = retv['uflxlw']
        rd.dflxlw = retv['dflxlw']

        return rd
    # }}}
# }}}

class RRTMG_SW(params.SW):
# {{{
    prmname = 'RRTMG'

    # Define parameter model, serialization options
    def __init__(self, Nl, Np=1, **kwargs):
    # {{{
        lists = []
        params.SW.__init__(self, self.prmname, Nl, Np, lists=lists, **kwargs)
    # }}}

    def run(self):
    # {{{
        def sanitize(a): return np.asfortranarray(a[:], 'd')

        pf   = sanitize(self.pres)
        ph   = sanitize(self.phalf)
        t    = sanitize(self.T)
        tsfc = sanitize(self.Tsfc)

        co2  = sanitize(self.CO2)
        h2o  = sanitize(self.H2O)
        o3   = sanitize(self.O3)

        scon = self.scon
        cosz = sanitize(self.cosz)
        alb  = sanitize(self.alb)

        if np.any(np.diff(pf)) < 0. or np.any(np.diff(ph) < 0.):
            raise ValueError('Pressure values must be strictly increasing.')

        for chi, name in zip([co2, h2o, o3], ['CO2', 'H2O', 'O3']):
            if np.any(chi < 0.) or np.any(np.isnan(chi)):
                raise ValueError('%s values must be finite and non-negative.' % name)

        rrtmg.init(self.cpair)

        retv = rrtmg.rrtmg_sw(pf, ph, t, tsfc, scon, cosz, alb, co2, h2o, o3)

        rd = self._swout()
        rd.swhr   = retv['swhr']
        rd.uflxsw = retv['uflxsw']
        rd.dflxsw = retv['dflxsw']

        return rd
    # }}}
# }}}


#Nl = 80
#zh = np.linspace(60, 0, Nl+1)
#ph = 1000.*np.exp(-zh / 7.)
#pf = np.sqrt(ph[:-1] * ph[1:]) 

#prm = RRTMG_LW(Nl, 1, pres=pf, phalf=ph)




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
