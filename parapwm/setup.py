from distutils.core import setup, Extension

module = Extension('parapwm_c',
                    sources=['parapin_py.c'],
                    include_dirs=['../'],
                    libraries=['parapin'],
                    library_dirs=['../'])

setup(name = 'ParaPWM',
      version = '1.0',
      py_modules = ['parapwm'],
      ext_modules = [module])

