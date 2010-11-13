import os

# get build dir option
variant_dir = GetOption('variant_dir')

# write cache files to build directory
SConsignFile(variant_dir + '/.sconsign.dblite')

# actually build things
SConscript("main.scons", variant_dir=variant_dir, duplicate=False)
