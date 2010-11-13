from SCons.Script import AddOption

# override build directory
AddOption('--variant-dir', dest='variant_dir',
          nargs=1, type='string',
          action='store', metavar='DIR',
          help='build directory',
          default='.build')

# show variables
AddOption('--help-variables', dest='help_variables',
          action='store_true', help='show construction variables',
          default=False)

