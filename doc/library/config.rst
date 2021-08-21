config - 设置的读写
==============================

前言
---------
在 Xenon 0.3.2 以前，我们使用的是手写的 `XenonConfigTemplate`，
运用装饰器来达到 “所见即所得” 的效果。

但是，这太耗费精力了，而且也难以维护，还大大增加了代码复杂度。

直到我们发现 `pydantic <https://github.com/samuelcolvin/pydantic/>`_ 这个库。

文档
---------
.. automodule:: lib.config
    :members:
