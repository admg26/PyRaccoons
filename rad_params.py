import numpy as np
from os.path import expanduser

class Param():
  # {{{
    def __init__(self, name, default, form=None, dtype=None, trig=None, show=False):
      # {{{
      self.name = name
      self.default = default
      self.form = form
      self.trig = trig
      self.show=show
      if (hasattr(default, '__len__') and type(default) is not str):
        self.value = default.copy()
      else: 
        self.value = default

      if dtype is None: self.dtype = self._gettype(default) # Auto-detect dtype
      else: self.dtype = dtype


      assert self.dtype in [np.int32, np.float32, np.str]
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
        pass
    # }}} 

    def write(self):
    # {{{
        return self._fmt.format(self.value)
    # }}}

    def write_default(self):
    # {{{
        import re
        width = int(re.findall(":>(\d+).",self._fmt)[0])
        return width*' '               
    # }}}

#    def _getfmt(self, dtype, form):
# {{{
#      return '{:{width}.{prescision}f}'   

      #if dtype is np.bool: return '.{!r}.'
      #elif dtype is np.int32: return '{:d}'
      #elif dtype is np.float32: return '{:.10g}'
      #else: assert False
# }}}

    def _gettype(self, value):
      # {{{
      if (hasattr(value, '__len__') and type(value) is not str): v = value[0]
      else: v = value

      if type(v) is int: return np.int32
      elif type(v) is bool: return np.bool
      elif np.isreal(v): return np.float32
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
        params.append(IGCMParam.copy(v))
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
        if p.display():
          s += p.write()
        else:
          s += p.write_default() 
      return s
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
        s += l.write() + '\n'

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

class LW(ParamSet):
  # {{{
    def __init__(self, name, NL, **kwargs):
      # {{{  
      lw3_6 = lwrecord3_6(self,NL)
      lw3_6_ordered = lw3_6.prm_dict.values()
      lw3_6_ordered.sort(key=lambda p:p._order)

      lists = [lwrecord1_2(self),lwrecord1_4(self),lwrecord3_1(self),lwrecord3_2(self),\
          lwrecord3_3B1(self,NL),lwrecord3_4(self,NL),lwrecord3_5(self),lwrecord3_6(self,NL)]

      ParamSet.__init__(self, name, lists, **kwargs)
      self.__dict__['lw3_6ordered'] = lw3_6_ordered
# }}} 

    def __getinitargs__(self):
      # {{{
      return (self.name, self.NL)
# }}}

    def _buildetaaxes(self):
      # {{{
      import igcm as ig
      import pygeode as pyg

      etah = self.etah.copy()
      etahp = np.concatenate([[self.etatop], etah, [1.]])
      eta = 0.5 * (etahp[:-1] + etahp[1:])

      Bh = ig.hyb_B(etah, self.etatop, self.etar)
      B = ig.hyb_B(eta, self.etatop, self.etar)
      etah = pyg.Hybrid(etah, etah - Bh, Bh)
      eta = pyg.Hybrid(eta, eta - B, B)

      return etah, eta
# }}}
    def write(self):
      # {{{

      s = ''
      for l in self._lists:
        if l.name in ['lwrecord1_2','lwrecord1_4','lwrecord2_1','lwrecord3_1',\
                     'lwrecord3_2','lwrecord3_3A','lwrecord3_4','lwrecord3_5']:
          s += l.write()
          s += '\n'

        elif l.name in ['lwrecord3_3B1']:
          for i in range(self.IBMAX):
            s += self.ZBND._fmt.format(self.ZBND[i])
            if i % 8 == 7: s += '\n'

        elif l.name in ['lwrecord3_3B2']:
          for i in range(self.IBMAX):
            s += self.PBND._fmt.format(self.ZBND[i])
            if i % 8 == 7: s += '\n'

        elif l.name in ['lwrecord3_6']:
          rowfmt = '' 
          params = l.prm_dict.values()
          params = self.lw3_6ordered
          for p in params[:self.NMOL]:
            if p.display(): 
              rowfmt += p._fmt
            else: 
              rowfmt += p.write_default()

          for i in range(self.IMMAX):
              s += rowfmt.format(*[m.value[i] for m in params[:self.NMOL]])
              s += '\n'

      return s
# }}}

class SW(ParamSet):
  # {{{
   def __init__(self, name, NL, **kwargs):
     # {{{  
      lists = [swprm(self, NL)]

      ParamSet.__init__(self, name, lists, **kwargs)
# }}} 

   def __getinitargs__(self):
   # {{{
      return (self.name, self.NL)
   # }}}
# }}}

def lwrecord1_2(pset):
  # {{{
    return Namelist('lwrecord1_2', \
        [Param('IATM',   1, form='{:>50d}',show=True),\
        Param('IXSECT', 0, form='{:>20d}',show=True),\
        Param('ISCAT',  0, form='{:>13d}',show=True),\
        Param('NUMANGS',4, form='{:>2d}',show=True),\
        Param('IOUT',   0, form='{:>5d}',show=True),\
        Param('ICLD',   0, form='{:>5d}',show=True)],\
        pset)
    # }}}

def lwrecord1_4(pset):
  # {{{
    return Namelist('lwrecord1_4', \
        [Param('TBOUND',    200.0,  form='{:>10.3e}',show=True),\
        Param('IEMIS',     0,      form='{:>2d}',show=True),\
        Param('IREFLECT',  0,      form='{:>3d}',show=True),\
        Param('SEMISS',    1,      form='{:>5.3e}',show=True)],\
        pset)
    # }}}

def lwrecord2_1(pset, NL):
  # {{{
    #Not complete. We do not need this right now since IATM=1
    def frm_trig(v, pset):
      if v == 0:
        pset.PAVE._fmt = '{:>10.4f}'
      elif v == 1:
        pset.PAVE._fmt = '{:>15.7e}'
      else:
        pset.force('PAVE', 0)
        raise ValueError('Only accepted values for IFORM are 0 and 1; setting to 0.')

    return Namelist('lwrecord2_1', \
        [Param('IFORM',     0,  form='{:>2d}', trig=frm_trig), \
        Param('NLAYRS',    NL, form='{:>3d}'),\
        Param('NMOL',      7,  form='{:>5d}'),\
        Param('PAVE',      np.zeros(NL, 'd'), form='{:>10.4f}')],\
        pset)
    # }}}

def lwrecord3_1(pset):
  # {{{
    #IATM=1

    return Namelist('lwrecord3_1', \
        [Param('MODEL',     0,  form='{:>5d}',show=True), \
        Param('IBMAX',     0,  form='{:>10d}',show=True),\
        Param('NOPRNT',    0,  form='{:>10d}',show=True),\
        Param('NMOL',      7,  form='{:>5f}',show=True),\
        Param('IPUNCH',    0,  form='{:>5d}',show=True),\
        Param('MUNITS',    0,  form='{:>5d}',show=True),\
        Param('RE',        0,  form='{:>10.3f}',show=True),\
        Param('CO2MX',     0,  form='{:>30.3f}',show=True),\
        Param('REF_LAT',   0.0,form='{:>10.3f}',show=True)],\
        pset)
    # }}}

def lwrecord3_2(pset):
  # {{{
   #IATM=1
    def frm_trig(v, pset):
      if (pset.IBMAX > 0 and v < pset.HBOUND):
        raise ValueError('Layer values in km. Top of the atmosphere must be higher than the surface')
      elif (pset.IBMAX < 0 and v > pset.HBOUND):
        raise ValueError('Layer values in mb. Top of the atmosphere must be higher than the surface')

    return Namelist('lwrecord3_2', \
        [Param('HBOUND',    0.0,form='{:>10.3f}', show=True), \
        Param('HTOA',      0.0,form='{:>10.3f}', trig=frm_trig, show=True)],\
        pset)
    # }}}

def lwrecord3_3A(pset):
  # {{{
    #IATM=1
#    def col_trig(v,pset):

     return Namelist('lwrecord3_3A', \
        [Param('AVTRAT',     0,  form='{:>10.3f}', show=True), \
        Param('TDIFF1',     0,  form='{:>10.3f}', show=True),\
        Param('TDIFF2',     0,  form='{:>10.3f}', show=True),\
        Param('ALTD1',      0,  form='{:>10.3f}', show=True),\
        Param('ALTD1',      0,  form='{:>10.3d}', show=True)],\
        pset, active=True)
    # }}} 

def lwrecord3_3B1(pset,NL):
  #{{{
    #IATM=1 and IBMAX > 0
    return Namelist('lwrecord3_3B1', \
        [Param('ZBND', np.zeros(NL-1, 'd'), form='{:>10.3f}', show=True)], \
        pset, active=False)
    # }}}

def lwrecord3_3B2(pset,NL):
  # {{{
    #IATM=1 and IBMAX < 0
    return Namelist('lwrecord3_3B2', \
        [Param('PBND', np.zeros(NL-1, 'd'), form='{:>10.3f}', show=True)], \
        pset, active=False)

    # }}}

def lwrecord3_4(pset,NL):
  # {{{
    #IATM=1 and model =0 

    return Namelist('lwrecord3_4', \
        [Param('IMMAX', NL, form='{:>5d}', show=True), \
        Param('HMOD',   '', form='{:24s}', show=True)],\
        pset)
    # }}}

def lwrecord3_5(pset):
  # {{{
    #IATM=1 and model =0 
    def show_trig(v,pset):
        if len(v) != pset.NMOL:
          raise ValueError("Flags JCHAR for all the '%s' molecues not set or too many flags set. Flags: '%s'" % (pset.NMOL, v))

        for i in range(len(v)):
          if v[i].isdigit():
            if pset.lw3_6ordered[i].show:
              pset.lw3_6ordered[i].show = False
              print("Setting '%s' to default value for Model = '%s'" % (pset.lw3_6ordered[i].name, v[i]))

          elif v[i] in ['A','B','C','D','E','F','G']:
            if not pset.lw3_6ordered[i].show:
              raise ValueError("Values for '%s' must be set and show set to True" % (pset.lw3_6ordered[i].name))

          else:
            raise ValueError("Flag values for JCHAR must be 1-6, A-G")

    return Namelist('lwrecord3_5', \
        [Param('ZM',    0,  form='{:>10.3e}',   show=True), \
        Param('PM',     0,  form='{:>10.3e}',   show=True), \
        Param('TM',     200,form='{:>10.3e}',   show=True), \
        Param('JCHARP', 'A',form='{:>6s}',      show=True), \
        Param('JCHART', 'A', form='{:>s}',      show=True), \
        Param('JCHAR',  'AAA6666', form='{:>31s}',trig = show_trig, show=True)], \
        pset)
    # }}}

def lwrecord3_6(pset,NL):
  # {{{
    #IATM=1 and model =0 

    return Namelist('lwrecord3_6', \
        [Param('VMOLH2O', np.zeros(NL,'d'), form='{:>10.3e}', show = True), \
        Param('VMOLCO2', np.zeros(NL,'d'), form='{:>10.3e}', show = True), \
        Param('VMOLO3', np.zeros(NL,'d'), form='{:>10.3e}', show = True), \
        Param('VMOLN2O', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLCO', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLCH4', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLO2', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLNO', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLSO2', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLNO2', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLNH3', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLHNO3', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLOH', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLHF', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLHCL', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLHBR', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLHI', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLCLO', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLOCS', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLH2CO', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLHOCL', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLN2', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLHCN', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLCH3CL', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLH2O2', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLC2H2', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLC2H6', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLPH3', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLCOF2', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLSF6', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLH2S', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLHCOOH', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLEMPTY', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLEMPTY', np.zeros(NL,'d'), form='{:>10.3e}'), \
        Param('VMOLEMPTY', np.zeros(NL,'d'), form='{:>10.3e}')], \
        pset)
    # }}}

def swprm(pset, NL):
  # {{{
    def nl_trig(v, pset): 
      pass

    return Namelist('SW', \
        [Param('NL', 50, trigger=nl_trig, show=True), \
        Param('temp', 250.*np.ones(NL)), \
        Param('pres', 10**np.linspace(3., 1., NL)), \
        Param('albedo', 0.3)], \
        pset)
    # }}}
