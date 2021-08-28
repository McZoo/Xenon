开始使用
=================

在开始使用 `Xenon` 之前， 请自行配置
`MCL <https://github.com/iTXTech/mirai-console-loader>`_
和 `mirai-api-http v1.12 <https://github.com/project-mirai/mirai-api-http>`_ 。

完成后，切换至本 repo 的根目录下，使用 `pip install -r requirements.txt` 安装好依赖项。

之后可以通过修改 `plugins` 文件夹增减插件。

接着，通过执行根目录下 `utils/dependency_resolve.py` 查看或导出当前安装插件需要的依赖项。

注：某些图片库可能需要另外安装 `ffmpeg` 等外部软件，请自行解决问题。

完成准备工作后，通过 `python main.py` 开始使用 `Xenon` 吧！
