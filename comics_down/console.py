#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
comics-down Console (控制台)
@module console
@file console.py
"""

import sys
import os
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.base_tools.run_tool import RunTool
from HiveNetLib.simple_console.server import ConsoleServer
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))


__MOUDLE__ = 'console'  # 模块名
__DESCRIPT__ = u'comics-down Console (控制台)'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2019.12.3'  # 发布日期


def main(**kwargs):
    # 判断是直接通过命令行执行, 还是通过控制台
    _cmd_opts = RunTool.get_kv_opts()
    if len(sys.argv) > 1 and not ('help' in _cmd_opts.keys() or 'shell_cmd' in _cmd_opts.keys() or 'shell_cmdfile' in _cmd_opts.keys()):
        # 有命令参数，但是不是外部命令行的标准参数，则认为是在外部命令行执行，将其转换为shell_cmd模式
        sys.argv.remove(sys.argv[0])
        _shell_cmd = 'shell_cmd=["download %s"]' % ' '.join(sys.argv).replace('\\', '\\\\')
        sys.argv.clear()
        sys.argv.append('console.py')
        sys.argv.append(_shell_cmd)

    # 通过控制台执行
    ConsoleServer.console_main(
        execute_file_path=os.path.realpath(FileTool.get_file_path(__file__)),
        **kwargs
    )


if __name__ == '__main__':
    main()
