#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
http通用下载驱动
@module http_down_driver
@file http_down_driver.py
"""

import os
import sys
import ssl
from HiveNetLib.base_tools.net_tool import NetTool
from HiveNetLib.base_tools.file_tool import FileTool
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import BaseDownDriverFW, Tools


# 取消全局ssl验证
ssl._create_default_https_context = ssl._create_unverified_context


class HttpDownDriver(BaseDownDriverFW):
    """
    普通http连接的图片下载驱动
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
        return 'http'

    @classmethod
    def download(cls, file_url: str, save_file: str, extend_json: dict = None, **para_dict):
        """
        下载文件
        (需继承类实现，如果下载失败应抛出异常, 正常执行完成代表下载成功)

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} extend_json=None - 要送入下载驱动的扩展信息
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来, 支持参数如下：
            down_proxy
            down_cookie
            use_break_down
            overtime
            connect_retry
            verify
            show_rate
        """
        _save_file = os.path.realpath(save_file)

        # 代理服务器设置
        _proxy = {}
        if para_dict.get('down_proxy', '') != '':
            _proxy = Tools.get_proxy(para_dict['down_proxy'])

        # cookie
        _cookies = {}
        if para_dict.get('down_cookie', '') != '':
            _cookies = Tools.get_cookie_from_file(para_dict['down_cookie'])

        NetTool.download_http_file(
            file_url, filename=FileTool.get_file_name(_save_file),
            path=FileTool.get_file_path(_save_file),
            is_resume=(para_dict.get('use_break_down', 'y') == 'y'),
            headers={'User-agent': 'Mozilla/5.0'},
            connect_timeout=float(para_dict.get('overtime', '30')),
            proxies=_proxy,
            retry=int(para_dict.get('connect_retry', '3')),
            verify=(para_dict.get('verify', 'y') == 'y'),
            cookies=_cookies,
            show_rate=(para_dict.get('show_rate', 'n') == 'y')
        )
