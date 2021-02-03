#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
媒体文件下载工具
@module media_down
@file media_down.py

@example
    # 简单模式
    python media_down.py url=https://??.html file=E:\m3u8\test.mp4

    # 使用代理
    python media_down.py url=http://www.edddh.com/vod/daojianshenyuxuliezhizheng/2-1.html file=D:\动漫下载\刀剑神域-序列之争.mp4 proxy=http://127.0.0.1:9000
"""

import sys
import os
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.base_tools.run_tool import RunTool
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from comics_down.lib.auto_analyse import AnalyzeTool
from comics_down.lib.m3u8_downloader import M3u8Downloader
from comics_down.down_driver.init_aria2 import Aria2Driver
from comics_down.down_driver.init_down_driver import HttpDownDriver

__MOUDLE__ = 'media_down'  # 模块名
__DESCRIPT__ = u'媒体文件下载工具'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.10.25'  # 发布日期


def main(**kwargs):
    # 判断是直接通过命令行执行, 还是通过控制台
    _cmd_opts = RunTool.get_kv_opts()
    _types = _cmd_opts.get('types', 'm3u8,mp4').split(',')
    _down_url = _cmd_opts['url']
    _ext = FileTool.get_file_ext(_down_url).lower()
    _file = _cmd_opts.get('file', '')

    # 剔除不传入后端的参数
    for _key in ('types', 'url', 'file'):
        _cmd_opts.pop(_key, None)

    if _ext not in _types:
        # 是页面，通过自动分析获取下载资源
        _down_url = AnalyzeTool.get_media_url(
            _down_url, _types, **_cmd_opts
        )
        if _down_url is None:
            raise RuntimeError('no media found!')

        print('Down url: %s' % _down_url)
        _ext = FileTool.get_file_ext(_down_url).lower()

    # 处理保存文件名
    if _file == '':
        _file = os.path.split(_down_url)[1]
        if _ext == 'm3u8':
            _file = _file[0:-4] + 'mp4'

    # 下载文件
    if _ext == 'm3u8':
        M3u8Downloader(
            _file, _down_url,
            process_num=int(_cmd_opts.get('job_worker', '3')),
            is_resume=(_cmd_opts.get('use_break_down', 'y') == 'y'),
            retry=int(_cmd_opts.get('connect_retry', '3'))
        )
    else:
        # 直接使用aria2下载
        try:
            Aria2Driver.download(
                _down_url, _file, **_cmd_opts
            )
        except:
            # 下载出现异常，尝试用wget再下载一次
            _cmd_opts['use_break_down'] = 'n'
            _cmd_opts['show_rate'] = 'y'
            _cmd_opts['verify'] = 'n'
            HttpDownDriver.download(
                _down_url, _file, **_cmd_opts
            )


if __name__ == '__main__':
    main()
