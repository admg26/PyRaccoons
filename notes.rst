

PyRaccoons 0.1
=================================

PyRaccoons is a python wrapper for column radiative transfer parameterizations
used to determine profiles of atmospheric radiative rates. The intent is to
provide a generic interface to the variety of existing radiative codes so that
users can easily swap out one radiative code for another. No radiative transfer
calculations are carried out directly by PyRaccoons.

The main feature is the definition of an set of extensible python classes which
contain the input data required to compute radiatie transfer (mostly profiles
of temperature, pressure, and radiatively active constituents) as well as the
output data produced by the underlying codes. An interface is provided so that
the user can easily write code that is unaware of any details of a specific
parameterization - and thus can easily swap out one for another.

Structure of code
-------------------------------
The core classes generic to all parameterizations are defined in the file
params.py.  There are two categories of basic classes - longwave and shortwave
'input' classes, which contain the profiles etc. required as input to the
calculations, and longwave and shortwave 'output' classes which contain the
output. 

Each of these are ultimately subclassed from a core datastructure
(ParamSet) which acts a bit like a C-style struct (or class), in that the class
has a specific defined set of parameters whose dimensions and data types are
pre-determined. This is used as the basis of the 'extensible' behaviour: any
instance of the class RadParams will have arrays for defining profiles of
temperature, pressure and radiative constituents. Instances of the class LW
inherit these profiles, but also include a parameter for surface emissivity.
Finally, instances of the RRTM_LW subclass inherit all of this, but also
include specific parameters for specifying the details of the RRTM longwave
parameterization.  All input wrapper classes can be guaranteed to have a
certain subset of details common to all parameterizations. 

Similarly, the output classes define a minimal set of output parameters (at the
moment upward and downward fluxes, and heating rates) common to all
parameterizations while further output is contained by specific subclasses.

The RadParams class is also intended to provide some common 'utility'
functions, including generic writing and reading routines so that the data can
be serialized in a standard way. There is the beginnings of code to write out
NetCDF files, and ascii files should be straightforward. The behaviour of the
underlying ParamSet, Namelist, and Param classes were originally intended to
abstract Fortan namelists; there are some behaviours we might think about
changing, in particular defining a bit more rigidly the notion of 'dimensions.'
For example we might want to be able to define variables over a set of levels,
a set of profiles, and a set of spectral bands; these should have consistent
sizes for a given instance. It also might be good to have a clear notion of
units that is well respected by the underlying codes so that one doesn't have
to guess about these things, and so that when the data is serialized this can
be added (e.g. as an attribute on the variables, which will ideally be
CF-compliant).

At the moment there are two parameterizations that are wrapped - RRTMG and
RRTM. The former uses a cython wrapper to the rrtmg gcm code, whereas the RRTM
wrapper writes ascii files for each profile, executes the standalone
executable, then reads in the ascii output. Given that the latter is probably
where we'll start for the rest of the paramerizations we might consider making
some of the details common (i.e. providing some of the code in RadParams with
hooks for the subclasses to invoke their own behaviour. Maybe. I haven't done
any speed tests on any of this yet. It would be good (and probably not too much 
work) to write an ascii interface for the rrtmg code as well.

Finally, pyracc.py is the intended top level interface - the idea is to write
some simple python functions there that act as an interface to the specific
parameterizations.

