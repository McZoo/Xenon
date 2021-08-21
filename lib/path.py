# coding=utf-8
"""
Xenon 相关路径获取，同时自动创建必要路径

root: 根路径

config: 设置文件所在路径

log: 日志文件所在路径

plugin: 插件所在路径

database: 数据库文件所在路径
"""
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
