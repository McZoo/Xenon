from os import makedirs
from os.path import abspath, join, exists

root = abspath(join(__file__, "..", ".."))
config = abspath(join(root, "config"))
log = abspath(join(root, "log"))
plugin = abspath(join(root, "plugin"))
database = abspath(join(root, "database"))

if not exists(config):
    makedirs(config)

if not exists(log):
    makedirs(log)

if not exists(plugin):
    makedirs(plugin)

if not exists(database):
    makedirs(database)
