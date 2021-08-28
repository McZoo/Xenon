# 改动记录

## 0.5.0
为 `lib.control.Interval` 使用 `asyncio.Lock` 上锁

## 0.4.5
添加了三个插件，修复了一些逻辑问题

## 0.4.4
修复了一些 bug

添加了基于 `headless_decorator` 的权限控制和调用间隔控制

## 0.4.3
修复了一些 bug

添加了 `StarGazer4K` 提供的毒鸡汤插件

添加依赖解析器

## 0.4.2
修复了 cave 插件的 bug

向回声洞添加查询功能

## 0.4.1
更新了 database 模块使其更易用

添加了简单的骰子插件

## 0.4.0
兼容 Saya 插件

重写 plugin 模块

## 0.3.3
使用 loguru 库代替 log 模块

## 0.3.2
重写config库

进一步完善文档

## 0.3.1
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
