import numpy as np
import params
import subprocess, os

class RRTM_LW(params.LW):
# {{{
    ''' Parent class for longwave column radiative transfer calculations. '''
    prmname = 'RRTM'
    ascpath = './rrtm_ascii/'

    # Define parameter model, serialization options
    def __init__(self, Nl, Np=1, **kwargs):
    # {{{
        lists = [rrtmprofile(self, Nl, Np), rrtmlwopt(self)]
        params.LW.__init__(self, self.prmname, Nl, Np, lists=lists, **kwargs)
    # }}}

    def calc_broad(self):
    # {{{
        # Convert water molar fraction to volume mixing ratio
        qv = self.H2O / (1. - self.H2O)

        # Compute pressure step in hPa 
        dp = (self.phalf[:, 1:] - self.phalf[:, :-1])

        # Unit factor: 100 Pa/hPa * 1000g / kg * (1 m / 100cm)**2 = 10
        self.Broad = 10. * dp * self.NA * (1. + qv * self.rdh2o) / (self.g * self.md * (1. + qv))
    # }}}

    def write_input(self, i):
    # {{{
        fn = self.ascpath + self.name + '_input_%d' % i

        ruler      = \
'''0        1         2         3         4         5         6         7         8         9
123456789-123456789-123456789-123456789-123456789-123456789-123456789-123456789-123456789-123456789-
'''
        lwrec1_1   = '${CXID:<79}\n'
        lwrec1_2   = '{IATM:>50d}{IXSECT:>20d}{ISCAT:>13d}{NUMANGS:>2d}{IOUT:>5d}{ICLD:>5d}\n'
        lwrec1_4   = '{TBOUND:>10.3f}{IEMIS:>2d}{IREFLECT:>3d}'
        semiss     = '{:>5.3f}'
        lwrec2_1   = '{IFORM:>2d}{NLAYRS:>3d}{NMOL:>5d}\n'
        lwrec2_11A = '{PAVE:>15.7e}{TAVE:>10.4f}{PZM:>31.3f}{TZM:>7.2f}{PZ:>15.3f}{TZ:>7.2f}\n'
        lwrec2_11B = '{PAVE:>15.7e}{TAVE:>10.4f}{PZ:>53.3f}{TZ:>7.2f}\n'
        lwrec2_12  = '{H2O:>15.7e}{CO2:>15.7e}{O3:>15.7e}{N2O:>15.7e}{CO:>15.7e}{CH4:>15.7e}{O2:>15.7e}{BROAD:>15.7e}\n'

        lwrec3_1   = '{MODEL:>5d}{IBMAX:>10d}{NOPRNT:>10d}{NMOL:>5d}{IPUNCH:>5d}{MUNITS:>5d}{RE:>10.3f}{CO2MX:>30.3f}{REFLAT:>10.3f}\n'
        lwrec3_2   = '{HBOUND:>10.3f}{HTOA:>10.3f}\n'
        lwrec3_3B  = '{:>10.3f}'
        lwrec3_4   = '{INMAX:>5d}\n'

        l1_1d  = dict(CXID = 'TEST OUTPUT')
        l1_2d  = dict(IATM = 0, IXSECT = 0, ISCAT = 0, NUMANGS = 4, IOUT = 0, ICLD = 0)
        l1_4d  = dict(TBOUND = self.Tsfc[i], IEMIS = 1, IREFLECT = 0)
        l2_1d  = dict(IFORM = self.iform, NLAYRS = self.Nl, NMOL = 7)
        l2_11d = dict(PAVE  = self.pres [i, self.Nl - 1], \
                      TAVE  = self.T    [i, self.Nl - 1], \
                      PZM   = self.phalf[i, self.Nl],     \
                      TZM   = self.Thalf[i, self.Nl],     \
                      PZ    = self.phalf[i, self.Nl - 1], \
                      TZ    = self.Thalf[i, self.Nl - 1])
        l2_12d = dict(H2O   = self.H2O  [i, self.Nl - 1], \
                      CO2   = self.CO2  [i, self.Nl - 1], \
                      O3    = self.O3   [i, self.Nl - 1], \
                      N2O   = self.N2O  [i, self.Nl - 1], \
                      CO    = self.CO   [i, self.Nl - 1], \
                      CH4   = self.CH4  [i, self.Nl - 1], \
                      O2    = self.O2   [i, self.Nl - 1], \
                      BROAD = self.Broad[i, self.Nl - 1])
        #l3_1d = dict(MODEL = 0, IBMAX = -self.Nl, NOPRNT = 0, NMOL = 3,\
                     #IPUNCH = 0, MUNITS = 0, RE = 0., CO2MX = 0., REFLAT = 0.)
        #l3_2d = dict(HBOUND = self.phalf[i,-1], HTOA = self.phalf[i,0])
        #l3_4d = dict(INMAX = -self.Nl = self.phalf[i,-1], HTOA = self.phalf[i,0])

        #fmts  = [self.lwrec1_1, self.lwrec1_2, self.lwrec1_4]
        #dicts = [l1_1d, l1_2d, l1_4d]

        with open(fn, 'w') as f:
            f.write(ruler)

            f.write(lwrec1_1.format(**l1_1d))

            f.write(lwrec1_2.format(**l1_2d))

            f.write(lwrec1_4.format(**l1_4d))

            if self.iemis == 1: # Use uniform surface emissivity
                f.write(semiss.format(self.emis[i]))
            elif self.iemis == 2: # Use band-dependent surface emissivity
                for e in self.bemis:
                    f.write(semiss.format(e))
            f.write('\n')

            f.write(lwrec2_1.format(**l2_1d))

            f.write(lwrec2_11A.format(**l2_11d))
            f.write(lwrec2_12 .format(**l2_12d))

            for k in range(self.Nl - 1)[::-1]:
                l2_11d['PAVE']  = self.pres [i, k]
                l2_11d['TAVE']  = self.T    [i, k]
                l2_11d['PZ']    = self.phalf[i, k]
                l2_11d['TZ']    = self.Thalf[i, k]
                l2_12d['H2O']   = self.H2O  [i, k]
                l2_12d['CO2']   = self.CO2  [i, k]
                l2_12d['O3']    = self.O3   [i, k]
                l2_12d['BROAD'] = self.Broad[i, k]
                f.write(lwrec2_11B.format(**l2_11d))
                f.write(lwrec2_12 .format(**l2_12d))

            f.write('%%%%%\n')

            #f.write(self.lwrec3_1.format(**l3_1d))

            #f.write(self.lwrec3_2.format(**l3_2d))

            #for k in range(self.Nl):
            #    f.write(self.lwrec3_3B.format(self.pres[i, k]))
            #    if k % 8 == 7: f.write('\n')

            #f.write(self.lwrec3_4.format(**l3_2d))

        return fn
    # }}}

    def read_output(self, fn):
    # {{{
        colnames = ['level', 'pres', 'uflxlw', 'dflxlw', 'netflxlw', 'lwhr']
        return np.genfromtxt(fn, skip_header=3, skip_footer=18, names = colnames, filling_values=0.)
    # }}}

    def run(self):
    # {{{
        # Allocate output arrays
        rd = self._lwout()

        # Compute 
        self.calc_broad()

        if os.path.exists('./INPUT_RRTM'):
            raise ValueError('Warning: existing INPUT_RRTM will be overwritten. Aborting.')

        for i in range(self.Np):
            # Loop through profiles, write input files for each
            ifn = self.write_input(i)

            # Link input_rrtm to each file, 
            os.symlink(ifn, './INPUT_RRTM')

            # call rrtm_lw
            subprocess.call("./rrtm_lw")

            # copy OUTPUT_RRTM to destination, unlink INPUT_RRTM
            ofn = self.ascpath + self.name + '_output_%d' % i
            os.rename('./OUTPUT_RRTM', ofn)
            os.unlink('./INPUT_RRTM')

            # read OUTPUT_RRTM into numpy array
            retv = self.read_output(ofn)
            rd.lwhr  [i, :] = retv['lwhr'][1:]
            rd.uflxlw[i, :] = retv['uflxlw']
            rd.dflxlw[i, :] = retv['dflxlw']

        return rd
    # }}}
# }}}

def rrtmprofile(pset, Nl, Nprof):
# {{{
    Nhl = Nl + 1
    one  = np.ones((Nprof, Nl), 'd')
    oneh = np.ones((Nprof, Nhl), 'd')
    ncax  = ('profiles', 'levels')
    ncaxh = ('profiles', 'hlevels')
    return params.Namelist('profile', \
        [params.Param('Thalf',  250. * oneh, ncaxes=ncaxh),\
         params.Param('Broad',         one,  ncaxes=ncax)],\
        pset)
# }}}

def rrtmlwopt(pset):
# {{{
    return params.Namelist('rrtmlwopt', \
        [params.Param('numangs',   4),\
         params.Param('iemis',     1),\
         #params.Param('bemis',     np.ones(16,'d')),\
         params.Param('iform',     1)],\
        pset)
# }}}

class RRTM_SW(params.SW):
# {{{
    prmname = 'RRTM'
    ascpath = './rrtm_ascii/'

    # Define parameter model, serialization options
    def __init__(self, Nl, Np=1, **kwargs):
    # {{{
        lists = [rrtmprofile(self, Nl, Np)]
        params.SW.__init__(self, self.prmname, Nl, Np, lists=lists, **kwargs)
    # }}}

    def calc_broad(self):
    # {{{
        # Convert water molar fraction to volume mixing ratio
        qv = self.H2O / (1. - self.H2O)

        # Compute pressure step in hPa 
        dp = (self.phalf[:, 1:] - self.phalf[:, :-1])

        # Unit factor: 100 Pa/hPa * 1000g / kg * (1 m / 100cm)**2 = 10
        self.Broad = 10. * dp * self.NA * (1. + qv * self.rdh2o) / (self.g * self.md * (1. + qv))
    # }}}

    def write_input(self, i):
    # {{{
        fn = self.ascpath + self.name + '_input_%d' % i

        ruler      = \
'''0        1         2         3         4         5         6         7         8         9
123456789-123456789-123456789-123456789-123456789-123456789-123456789-123456789-123456789-123456789-
'''
        swrec1_1   = '${CXID:<79}\n'
        swrec1_2   = '{IAER:>20d}{IATM:>30d}{ISCAT:>33d}{ISTRM:>2d}{IOUT:>5d}{ICLD:>5d}{IDELM:>4d}{ICOS:>1d}\n'
        swrec1_21  = '{JULDAT:>15d}{SZA:>10.4f}{ISOLVAR:>5d}'
        solvar     = '{:>5.3f}'
        swrec1_4   = '{IEMIS:>12d}{IREFLECT:>3d}'
        semiss     = '{:>5.3f}'
        swrec2_1   = '{IFORM:>2d}{NLAYRS:>3d}{NMOL:>5d}\n'
        swrec2_11A = '{PAVE:>15.7e}{TAVE:>10.4f}{PZM:>31.3f}{TZM:>7.2f}{PZ:>15.3f}{TZ:>7.2f}\n'
        swrec2_11B = '{PAVE:>15.7e}{TAVE:>10.4f}{PZ:>53.3f}{TZ:>7.2f}\n'
        swrec2_12  = '{H2O:>15.7e}{CO2:>15.7e}{O3:>15.7e}{N2O:>15.7e}{CO:>15.7e}{CH4:>15.7e}{O2:>15.7e}{BROAD:>15.7e}\n'

        sza = np.arccos(self.cosz[i]) * 180. / np.pi

        s1_1d  = dict(CXID = 'TEST OUTPUT')
        s1_2d  = dict(IAER = 0, IATM = 0, ISCAT = 0, ISTRM = 1, IOUT = 0, ICLD = 0, IDELM = 1, ICOS = 0)
        s1_21d = dict(JULDAT = 0, SZA = sza, ISOLVAR = 0)
        s1_4d  = dict(IEMIS = 1, IREFLECT = 0)
        s2_1d  = dict(IFORM = 1, NLAYRS = self.Nl, NMOL = 7)
        s2_11d = dict(PAVE  = self.pres [i, self.Nl - 1], \
                      TAVE  = self.T    [i, self.Nl - 1], \
                      PZM   = self.phalf[i, self.Nl],     \
                      TZM   = self.Thalf[i, self.Nl],     \
                      PZ    = self.phalf[i, self.Nl - 1], \
                      TZ    = self.Thalf[i, self.Nl - 1])
        s2_12d = dict(H2O   = self.H2O  [i, self.Nl - 1], \
                      CO2   = self.CO2  [i, self.Nl - 1], \
                      O3    = self.O3   [i, self.Nl - 1], \
                      N2O   = self.N2O  [i, self.Nl - 1], \
                      CO    = self.CO   [i, self.Nl - 1], \
                      CH4   = self.CH4  [i, self.Nl - 1], \
                      O2    = self.O2   [i, self.Nl - 1], \
                      BROAD = self.Broad[i, self.Nl - 1])

        #fmts  = [self.lwrec1_1, self.lwrec1_2, self.lwrec1_4]
        #dicts = [l1_1d, l1_2d, l1_4d]

        with open(fn, 'w') as f:
            f.write(ruler)

            f.write(swrec1_1.format(**s1_1d))

            f.write(swrec1_2.format(**s1_2d))
            f.write(swrec1_21.format(**s1_21d))
            # Solar source function scaling here
            f.write('\n')

            f.write(swrec1_4.format(**s1_4d))
            f.write(semiss.format(1. - self.alb[i]))
            f.write('\n')

            #if self.iemis == 1: # Use uniform surface emissivity
            #    f.write(semiss.format(self.emis[i]))
            #elif self.iemis == 2: # Use band-dependent surface emissivity
            #    for e in self.bemis:
            #        f.write(semiss.format(e))

            f.write(swrec2_1.format(**s2_1d))

            f.write(swrec2_11A.format(**s2_11d))
            f.write(swrec2_12 .format(**s2_12d))

            for k in range(self.Nl - 1)[::-1]:
                s2_11d['PAVE']  = self.pres [i, k]
                s2_11d['TAVE']  = self.T    [i, k]
                s2_11d['PZ']    = self.phalf[i, k]
                s2_11d['TZ']    = self.Thalf[i, k]
                s2_12d['H2O']   = self.H2O  [i, k]
                s2_12d['CO2']   = self.CO2  [i, k]
                s2_12d['O3']    = self.O3   [i, k]
                s2_12d['BROAD'] = self.Broad[i, k]
                f.write(swrec2_11B.format(**s2_11d))
                f.write(swrec2_12 .format(**s2_12d))

            f.write('%%%%%\n')

        return fn
    # }}}

    def read_output(self, fn):
    # {{{
        colnames = ['level', 'pres', 'uflxsw', 'difdflxsw', 'difdflxsw', 'dflxsw', 'netflxsw', 'swhr']
        return np.genfromtxt(fn, skip_header=5, skip_footer=14, names = colnames, filling_values=0.)
    # }}}

    def run(self):
    # {{{
        # Allocate output arrays
        rd = self._swout()

        # Compute 
        self.calc_broad()

        if os.path.exists('./INPUT_RRTM'):
            raise ValueError('Warning: existing INPUT_RRTM will be overwritten. Aborting.')

        for i in range(self.Np):
            # Loop through profiles, write input files for each
            ifn = self.write_input(i)

            # Link input_rrtm to each file, 
            os.symlink(ifn, './INPUT_RRTM')

            # call rrtm_sw
            subprocess.call("./rrtm_sw")

            # copy OUTPUT_RRTM to destination, unlink INPUT_RRTM
            ofn = self.ascpath + self.name + '_output_%d' % i
            os.rename('./OUTPUT_RRTM', ofn)
            os.unlink('./INPUT_RRTM')

            # read OUTPUT_RRTM into numpy array
            retv = self.read_output(ofn)
            rd.swhr  [i, :] = retv['swhr'][1:]
            rd.uflxsw[i, :] = retv['uflxsw']
            rd.dflxsw[i, :] = retv['dflxsw']

        return rd
    # }}}
# }}}

Nl = 80
zh = np.linspace(60, 0, Nl+1)
ph = 1000.*np.exp(-zh / 7.)
pf = np.sqrt(ph[:-1] * ph[1:]) 

prm = RRTM_SW(Nl, 11, pres=pf, phalf=ph)
prm.Tsfc = np.linspace(250, 300., 11)
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
