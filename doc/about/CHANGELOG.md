# 改动记录

# 0.3.1
添加“点歌”模块

构建文档基架

## 0.3.0
修复了一些bug

重写了Console模块，合并为一个线程

支持软重启

## 0.2.5
“回声洞”插件现在支持图片了

修复了第一次运行时缺少文件夹的问题

## 0.2.4
添加“回声洞”插件

## 0.2.3
添加“每日诗词”插件

## 0.2.2

添加“历史上的今天”插件，验证了package作为插件的可能性

## 0.2.1
Console 现在 post Command 更快了

现在要求插件的`main`函数是一个 [协程函数](https://docs.python.org/zh-cn/3/glossary.html#term-coroutine-function)

## 0.2.0

添加了 “关于Xenon” 插件

要求`PluginSpec`提供`doc_string`作为帮助文档来源

删除`TODO.md`，并更名为`ROADMAP.md`

添加`CHANGELOG.md`