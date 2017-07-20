import numpy as np
import params
import subprocess, os

class ZH(params.LW, params.SW):
# {{{
    ''' Parent class for longwave column radiative transfer calculations. '''
    prmname = 'ZH'
    ascpath = './zh_ascii/'

    # Define parameter model, serialization options
    def __init__(self, Nl, Np=1, **kwargs):
    # {{{
        lists = [zhprofile(self, Nl, Np)] #, zhlwopt(self)]
        params.SW.__init__(self, self.prmname, Nl, Np, lists=lists, **kwargs)
        params.LW.__init__(self, self.prmname, Nl, Np, lists=lists, **kwargs)
    # }}}

    def write_input(self, i):
    # {{{
        fn = self.ascpath + self.name + '_input_%d' % i
        surface_T  = '{TBOUND:>10.3f}\n'
        lwrec      = '{LEVEL:>10d}{TLEVEL:>15.6f}{H2O:>15.7e}{PLEVEL:>15.3f}{O3:>15.7e}\n'

        l1  = dict(TBOUND = self.Tsfc[i])
        l2  = dict(LEVEL   = i,     \
                   TLEVEL  = self.T    [i, self.Nl - 1], \
                   H2O     = self.H2O  [i, self.Nl - 1], \
                   PLEVEL  = self.pres [i, self.Nl - 1], \
                   O3      = self.O3   [i, self.Nl - 1])

        with open(fn, 'w') as f:
            f.write(surface_T.format(**l1))

            for k in range(self.Nl)[::-1]:
                l2['LEVEL']   = self.Nl - k
                l2['TLEVEL']  = self.T    [i, k]
                # Pressure in Pa
                l2['PLEVEL']  = self.pres [i, k]*100 
                l2['H2O']     = self.H2O  [i, k]
                l2['O3']      = self.O3   [i, k]
                f.write(lwrec.format(**l2))

        return fn
    # }}}

    def read_flux_lw(self, fn):
    # {{{
        colnames = ['uflxlw', 'dflxlw', 'netflxlw','pres']
        return np.genfromtxt(fn, names = colnames, filling_values=0.)
    # }}}

    def read_flux_sw(self, fn):
    # {{{
        colnames = ['dflxsw','uflxsw','netflxsw','pres']
        return np.genfromtxt(fn, names = colnames, filling_values=0.)
    # }}}

    def run(self):
    # {{{
        # Allocate output arrays
        rd_lw = self._lwout()
        rd_sw = self._swout()

        if os.path.exists('./INPUT_ZH'):
            raise ValueError('Warning: existing INPUT_ZH will be overwritten. Aborting.')

        for i in range(self.Np):
            # Loop through profiles, write input files for each
            ifn = self.write_input(i)

            # Link input_zh to each file, 
            os.symlink(ifn, './INPUT_ZH')

            # call zh_lw_sw
            subprocess.call("./zh_lw_sw")

            # copy OUTPUT_ZH to destination, unlink INPUT_ZH
            ofn_lw      = self.ascpath + rd_lw.name + '_output_lw_%d' % i
            ofn_sw      = self.ascpath + rd_sw.name + '_output_sw_%d' % i
            ofn_flux_lw = self.ascpath + rd_lw.name + '_output_fluxes_%d' % i
            ofn_flux_sw = self.ascpath + rd_sw.name + '_output_fluxes_%d' % i
            os.rename('./OUTPUT_ZH_LW', ofn_lw)
            os.rename('./OUTPUT_ZH_SW', ofn_sw)
            os.rename('./FLUXES_LW', ofn_flux_lw)
            os.rename('./FLUXES_SW', ofn_flux_sw)
            os.unlink('./INPUT_ZH')

            # read OUTPUT_ZH into numpy array
            rd_lw.lwhr = np.loadtxt(ofn_lw)
            rd_sw.swhr = np.loadtxt(ofn_sw)
            flux_lw = self.read_flux_lw(ofn_flux_lw)
            flux_sw = self.read_flux_sw(ofn_flux_sw)
            rd_lw.uflxlw[i, :]   = flux_lw['uflxlw']
            rd_lw.dflxlw[i, :]   = flux_lw['dflxlw']
            rd_sw.uflxsw[i, :]   = flux_sw['uflxsw']
            rd_sw.dflxsw[i, :]   = flux_sw['dflxsw']

        return {'rd_lw':rd_lw, 'rd_sw':rd_sw}
    # }}}
# }}}

def zhprofile(pset, Nl, Nprof):
# {{{
    Nhl = Nl + 1
    one  = np.ones((Nprof, Nl), 'd')
    ncax  = ('profiles', 'levels')
    return params.Namelist('profile', \
        [params.Param('T',  250. * one, ncaxes=ncax)],\
        pset)
# }}}

Nl = 100
zh = np.linspace(60, 0, Nl+1)
ph = 1000.*np.exp(-zh / 7.)
pf = np.sqrt(ph[:-1] * ph[1:]) 

prm = ZH(Nl, 1, pres=pf, phalf=ph)
prm.Tsfc = np.linspace(250, 300., 1)
rd = prm.run()

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
