import numpy as np

nctmap = {np.int64 : 'i', np.float64 : 'd'}

# Generic interface for defining extensible data structures
class Param():
# {{{
    def __init__(self, name, default, form=None, dtype=None, trigger=None, show=False, units=None, ncaxes=None):
    # {{{
        self.name = name
        self.default = default
        self.form = form
        self.trigger = trigger
        self.show=show
        self.units = units
        self.ncaxes = ncaxes
        if (hasattr(default, '__len__') and type(default) is not str):
            self.value = default.copy()
        else: 
            self.value = default

        if dtype is None: self.dtype = self._gettype(default) # Auto-detect dtype
        else: self.dtype = dtype

        assert self.dtype in [np.int64, np.float64, np.str]

        self.ncdtype = nctmap[self.dtype]

        self._fmt = form
    # }}}   

    @staticmethod
    def copy(prm):
    # {{{
        p = prm.__class__(prm.name, prm.default, prm.dtype, prm.trigger, prm.show)
        p.value = prm.value
        return p
    # }}}

    def __str__(self):
    # {{{
        vstr = ''

        if hasattr(self.value, 'shape'):
            vstr = repr(self.value.shape) + ' array'
        else:
            vstr = repr(self.value)


        return '%s = %s' % (self.name, vstr)
    # }}} 

    def __repr__(self):
    # {{{
        vstr = ''

        if hasattr(self.value, 'shape'):
            vstr = repr(self.value.shape) + ' array'
        else:
            vstr = repr(self.value)


        return '<Param: %s = %s>' % (self.name, vstr)
    # }}} 

    def _gettype(self, value):
    # {{{
        if (hasattr(value, '__len__') and type(value) is not str): v = np.ravel(value)[0]
        else: v = value

        if type(v) is int: return np.int64
        elif type(v) is bool: return np.bool
        elif np.isreal(v): return np.float64
        elif type(v) is str: return np.str
        else: assert False, 'Unrecognized variable type'
    # }}}

    def display(self):
    # {{{
        if self.show: return True
        if (hasattr(self.value, '__len__') and type(self.value) is not str):
            return not (self.value == self.default).all()
        else: return not self.value == self.default
    # }}}

    def setv(self, value):
    # {{{ 
        vdtype = self._gettype(value)
        if vdtype != self.dtype:
            raise AttributeError('Parameter %s is a %s, received a %s.' % \
                (self.name, self.dtype.__name__, vdtype.__name__))
        if hasattr(self.default, '__len__'):
            if hasattr(value, '__len__') and value.ndim == 1 and len(value) in self.default.shape:
                shp = np.ones(self.default.ndim, 'i')
                shp[self.default.shape.index(len(value))] = -1
                self.value[:] = value.reshape(*shp)
            else:
                self.value[:] = value
        else:
            self.value = value
        if self.trigger is not None: self.trigger(value, self.pset)
    # }}}
# }}}  

class Namelist():
  # {{{
    def __init__(self, name, params, pset, active=True):
      # {{{
      self.__dict__['name'] = name
      self.__dict__['pset'] = pset
      self.__dict__['active'] = active

      pdict = {}
      for i, p in enumerate(params): 
        p.__dict__['pset'] = pset
        p.__dict__['_order'] = i
        pdict[p.name] = p

      self.__dict__['prm_dict'] = pdict
# }}}

    @staticmethod
    def copy(nlist, pset):
      # {{{
      name = nlist.name
      active = nlist.active

      params = []
      porder = []
      for k, v in nlist.prm_dict.iteritems():
        params.append(Param.copy(v))
        porder.append(v._order)

      params = [params[i] for i in np.argsort(porder)]
      return nlist.__class__(name, params, pset, active)
# }}}

    def write(self):
    # {{{
        s = ''
        params = self.prm_dict.values()
        params.sort(key=lambda p:p._order)

        for p in params:
            s += str(p) + '\n'
        return s
    # }}}

    def write_nc(self, f):
    # {{{
        params = self.prm_dict.values()
        params.sort(key=lambda p:p._order)

        for p in params:
            p.write_nc(f)
    # }}}

    def __getattr__(self, name):
      # {{{
      if self.prm_dict.has_key(name): return self.prm_dict[name].value
      raise AttributeError("'%s' object has no parameter '%s'" % (self.__class__.__name__, name))
# }}}

    def __setattr__(self, name, value):
      # {{{
      if self.__dict__.has_key(name): self.__dict__[name] = value
      else: self.prm_dict[name].setv(value)
# }}}

    def __getitem__(self, name):
      # {{{
      if self.prm_dict.has_key(name): return self.prm_dict[name]
      raise AttributeError("'%s' object has no parameter '%s'" % (self.__class__.__name__, name))
# }}}
# }}}

class ParamSet():
  # {{{
    def __init__(self, name, lists, **kwargs):
      # {{{
      self.__dict__['_lists'] = lists
      self.set_name(name)
      for k, v in kwargs.iteritems():
        self.__setattr__(k, v)
# }}}

    def __getstate__(self):
      # {{{
      dict = self.__dict__.copy()
      lists = dict.pop('_lists')

      prm = {}
      for l in lists:
        if not l.active: continue
        for k, v in l.prm_dict.iteritems():
          if hasattr(v, '__len__'): 
            prm[k] = v.value.copy()
          else:
            prm[k] = v.value

      dict['_params'] = prm
      return dict
# }}}

    def __setstate__(self, dict):
      # {{{
      prm = dict.pop('_params')
      self.__dict__.update(dict)

      # Set all the flags first so that the correct namelists are active
      flags = [k for k in prm.keys() if k[0] == 'l']
      params = [k for k in prm.keys() if k[0] != 'l']
      for k in flags: self.__setattr__(k, prm[k])
      for k in params: self.__setattr__(k, prm[k])
# }}}

    @staticmethod
    def copy(other):
      # {{{
      # Construct base copy
      cpy = other.__class__(other.name)

      # Copy parameter lists
      lists = [Namelist.copy(l, cpy) for l in other._lists]

      # Reinitialize new copy with copied parameter lists
      ParamSet.__init__(cpy, cpy.name, lists)

      # Copy remainder of setup
      spc = ['_lists']
      for k, v in other.__dict__.iteritems():
        if k not in spc: cpy.__dict__[k] = v

      return cpy
# }}}

    def write(self):
      # {{{
      s = ''
      for l in self._lists:
          if l.active: s += l.write() + '\n'

      return s[:-1]
# }}}

    def __dir__(self):
      # {{{
        lst = self.__dict__.keys() + dir(self.__class__)
        for l in self._lists: 
          if l.active: lst += l.prm_dict.keys()
        return lst
# }}}

    def __getattr__(self, name):
      # {{{
      for l in self._lists:
        if l.name == name: return l
        if l.active and l.prm_dict.has_key(name): return l.__getattr__(name)
      raise AttributeError("'%s' object has no parameter '%s'" % (self.__class__.__name__, name))
# }}}

    def __setattr__(self, name, value):
      # {{{
      # Look for attribute in parameter list
      for l in [l for l in self._lists if l.active]:
        if l.prm_dict.has_key(name): 
          l.__setattr__(name, value)
          return

      if name == 'name':
        self.set_name(name)
      elif self.__dict__.has_key(name): 
        self.__dict__[name] = value
      else:
        raise AttributeError("'%s' object has no parameter '%s'" % (self.__class__.__name__, name))
# }}}

    def force(self, name, value):
      # {{{
      for l in self._lists:
        if l.prm_dict.has_key(name): 
          l.prm_dict[name].value = value
          return
      raise AttributeError("'%s' object has no parameter '%s'" % (self.__class__.__name__, name))
# }}}

    def set_name(self, name):
      # {{{
      self.__dict__['name'] = name
# }}}
# }}}

# Basic interface
class RadParams(ParamSet):
# {{{
    ''' Container class for parameters and data required for column radiative transfer calculations. '''

    # Define parameter model, serialization options
    def __init__(self, name, Nl, Np=1, lists=[], **kwargs):
    # {{{
        # By default include profiles of tracers, temperatures, pressures
        lists = [consts(self), profile(self, Nl, Np), tracers(self, Nl, Np)] + lists
        ParamSet.__init__(self, name, lists, **kwargs)

        self.__dict__['Nl'] = Nl
        self.__dict__['Np'] = Np
    # }}}

    def set_tracer(self, unit='ppmv', **kwargs):
        '''Sets tracer profiles. Performs unit conversions if need be.'''
        pass

    def write_ascii(self):
        pass

    def write_nc(self, fn):
        from scipy.io import netcdf as nc
        import os
        
        if os.path.exists(fn):
            ans = raw_input('%s already exists. Overwrite? y/[n]: ' % fn)
            if ans != 'y': return

        with nc.netcdf_file(fn, 'w') as f:
            f.createDimension('levels', self.Nl)
            f.createDimension('hlevels', self.Nl+1)
            f.createDimension('profiles', self.Np)

            levels = f.createVariable('levels', 'i', ('levels',))
            levels = np.arange(self.Nl)

            hlevels = f.createVariable('levels', 'i', ('hlevels',))
            hlevels = np.arange(self.Nl + 1)

            profiles = f.createVariable('profiles', 'i', ('profiles',))
            profiles = np.arange(self.Np)

            for l in self._lists:
                for p, prm in l.prm_dict.iteritems():
                    if prm.ncaxes is None:
                        # Scalar value, add as attribute to file
                        f.__setattr__(p, prm.value)
                    else:
                        v = f.createVariable(p, nctmap[prm.dtype], prm.ncaxes)
                        v[:] = prm.value


    def run(self):
        ''' Execute calculation on profile data. '''
        pass
# }}}

class LW(RadParams):
# {{{
    ''' Parent class for longwave column radiative transfer calculations. '''

    def __init__(self, prmname, Nl, Np=1, lists=[], **kwargs):
        self.__dict__['prmname'] = prmname
        name = '%s_LW_%dlevs_%dprofs' % (prmname, Nl, Np)
        lists = [lwbase(self, Nl, Np)] + lists
        RadParams.__init__(self, name, Nl, Np, lists, **kwargs)

    def _lwout(self):
        return LWOut(self.prmname, self.Nl, self.Np)
# }}}

class LWOut(ParamSet):
# {{{
    ''' Parent class for shortwave column radiative transfer calculations. '''

    def __init__(self, name, Nl, Np=1, lists=[], **kwargs):
        name = '%s_LWout_%dlevs_%dprofs' % (name, Nl, Np)
        lists = [lwout(self, Nl, Np)] + lists
        ParamSet.__init__(self, name, lists, **kwargs)
# }}}

class SW(RadParams):
# {{{
    ''' Parent class for shortwave column radiative transfer calculations. '''

    def __init__(self, prmname, Nl, Np=1, lists=[], **kwargs):
        self.__dict__['prmname'] = prmname
        name = '%s_SW_%dlevs_%dprofs' % (prmname, Nl, Np)
        lists = [swbase(self, Nl, Np)] + lists
        RadParams.__init__(self, name, Nl, Np, lists, **kwargs)

    def _swout(self):
        return SWOut(self.prmname, self.Nl, self.Np)
# }}}

class SWOut(ParamSet):
# {{{
    ''' Parent class for shortwave column radiative transfer output. '''

    def __init__(self, name, Nl, Np=1, lists=[], **kwargs):
        name = '%s_SWout_%dlevs_%dprofs' % (name, Nl, Np)
        lists = [swout(self, Nl, Np)] + lists
        ParamSet.__init__(self, name, lists, **kwargs)
# }}}

def tracers(pset, Nl, Nprof):
# {{{
    one = np.ones((Nprof, Nl), 'd')
    ncax = ('profiles', 'levels')
    return Namelist('tracers', \
        [Param('H2O', 3.e-6   * one, units = 'mol/mol', ncaxes=ncax),\
         Param('CO2', 380.e-6 * one, units = 'mol/mol', ncaxes=ncax),\
         Param('O3',  0.1e-6  * one, units = 'mol/mol', ncaxes=ncax),\
         Param('N2O', 0.3e-8  * one, units = 'mol/mol', ncaxes=ncax),\
         Param('CO',  0.5e-8  * one, units = 'mol/mol', ncaxes=ncax),\
         Param('CH4', 1.e-8   * one, units = 'mol/mol', ncaxes=ncax),\
         Param('O2',  0.21    * one, units = 'mol/mol', ncaxes=ncax)],\
        pset)
# }}}

def profile(pset, Nl, Nprof):
# {{{
    Nhl = Nl + 1
    one  = np.ones((Nprof, Nl), 'd')
    oneh = np.ones((Nprof, Nhl), 'd')
    onep = np.ones(Nprof, 'd')
    ncax  = ('profiles', 'levels')
    ncaxh = ('profiles', 'hlevels')
    ncaxp = ('profiles',)
    return Namelist('profile', \
        [Param('pres',          one,  ncaxes=ncax),\
         Param('phalf',        oneh, ncaxes=ncaxh),\
         Param('lat',     0. * onep,  ncaxes=ncaxp),\
         Param('lon',     0. * onep,  ncaxes=ncaxp),\
         Param('T',      250. * one,  ncaxes=ncax),\
         Param('Tsfc',  250. * onep, ncaxes=ncaxp)],\
        pset)
# }}}

def consts(pset):
# {{{
    return Namelist('profile', \
        [Param('cpair',   1003.),\
         Param('g',       9.807),\
         Param('md',      28.9660),\
         Param('rdco2',   0.658114),\
         Param('rdh2o',   1.607793),\
         Param('rdo3',    0.603428),\
         Param('NA',      6.022141e23)],\
        pset)
# }}}

def lwbase(pset, Nl, Nprof):
# {{{
    onep = np.ones(Nprof, 'd')
    ncaxp = ('profiles',)
    return Namelist('lwbase', \
        [Param('emis',  0.99 * onep, ncaxes=ncaxp)],\
        pset)
# }}}

def lwout(pset, Nl, Nprof):
# {{{
    Nhl = Nl + 1
    return Namelist('lwout', \
        [Param('lwhr',   np.zeros((Nprof, Nl ), 'd')),\
         Param('uflxlw', np.zeros((Nprof, Nhl), 'd')),\
         Param('dflxlw', np.zeros((Nprof, Nhl), 'd'))],\
        pset)
# }}}

def swbase(pset, Nl, Nprof):
# {{{
    onep = np.ones(Nprof, 'd')
    ncaxp = ('profiles',)
    return Namelist('swbase', \
        [Param('scon',  1368.22),\
         Param('emis',  0.99    * onep, ncaxes=ncaxp),\
         Param('cosz',  0.6     * onep, ncaxes=ncaxp),\
         Param('alb',   0.3     * onep, ncaxes=ncaxp)],\
        pset)
# }}}

def swout(pset, Nl, Nprof):
# {{{
    Nhl = Nl + 1
    return Namelist('swout', \
        [Param('swhr',   np.zeros((Nprof, Nl ), 'd')),\
         Param('uflxsw', np.zeros((Nprof, Nhl), 'd')),\
         Param('dflxsw', np.zeros((Nprof, Nhl), 'd'))],\
        pset)
# }}}
