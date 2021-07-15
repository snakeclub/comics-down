#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
you-get的下载驱动
@module youget_down_driver
@file youget_down_driver.py
"""

import os
import sys
import ssl
from urllib.parse import urlparse
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import BaseDownDriverFW, Tools

# 取消全局ssl验证
ssl._create_default_https_context = ssl._create_unverified_context


class YouGetDriver(BaseDownDriverFW):
    """
    使用you-get的下载驱动
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
        return 'you-get'

    @classmethod
    def download(cls, file_url: str, save_file: str, extend_json: dict = None, **para_dict):
        """
        下载文件
        (需继承类实现，如果下载失败应抛出异常, 正常执行完成代表下载成功)

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} extend_json=None - 要送入下载驱动的扩展信息
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来，支持的参数
            down_proxy

        """
        _path, _filename = os.path.split(save_file)
        _cmd = 'you-get -o "%s" -O "%s" -k' % (_path, _filename)

        # 添加代理参数
        if para_dict.get('down_proxy', '') != '':
            _proxy = Tools.get_proxy(para_dict['down_proxy'])
            _proxy_url = list(_proxy.values())[0]
            _cmd = '%s -x %s' % (_cmd, urlparse(_proxy_url).netloc)

        _shell = os.system('%s %s' % (_cmd, file_url))
        if _shell != 0:
            raise RuntimeError('download error')
