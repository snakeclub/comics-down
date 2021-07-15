#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
m3u8文件下载驱动
@module m3u8_down_driver
@file m3u8_down_driver.py
"""

import os
import sys
import json

from HiveNetLib.base_tools.file_tool import FileTool
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import BaseDownDriverFW, DriverManager
from comics_down.lib.m3u8_downloader import M3u8DownLoader


class M3u8Driver(BaseDownDriverFW):
    """
    使用m3u8的下载驱动
    """
    #############################
    # 需实现类继承的方法
    #############################
    @classmethod
    def get_down_type(cls):
        """
        返回该驱动对应的下载类型
        (需继承类实现)

        @return {str} - 下载类型字符串，如http/ftp
            注：系统加载的下载类型名不能重复
        """
        return 'm3u8'

    @classmethod
    def download(cls, file_url: str, save_file: str, extend_json: dict = None, **para_dict):
        """
        下载文件
        (需继承类实现，如果下载失败应抛出异常, 正常执行完成代表下载成功)

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} extend_json=None - 要送入下载驱动的扩展信息
            worker_num {int} - 下载小文件的工作线程数量，默认为3
            auto_retry {int} - 下载小文件的自动重试次数，默认为0
            down_task_overtime {float} - 下载小文件的超时时间，0代表不超时，默认为0
            down_driver_type {str} - 指定下载驱动的类型，默认为http
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
        """
        if extend_json is None:
            extend_json = dict()

        _down_driver = DriverManager.get_down_driver(
            extend_json.get('down_driver_type', 'http'),
            json.loads(para_dict.get('downtype_mapping', '{}'))
        )

        _save_file = save_file
        if FileTool.get_file_ext(_save_file) == '':
            _save_file = _save_file + '.mp4'

        _downloader = M3u8DownLoader(
            file_url, _save_file, worker_num=extend_json.get('worker_num', 3),
            auto_retry=extend_json.get('auto_retry', 0),
            down_driver=_down_driver,
            down_task_overtime=extend_json.get('down_task_overtime', 0),
            down_extend_json=extend_json,  # 共用同一个扩展信息字典
            **para_dict
        )

        _downloader.start_download(re_write=False)
