#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
ftp通用下载驱动
@module ftp_down_driver
@file ftp_down_driver.py
"""

import os
import sys
import HiveNetLib.base_tools.wget as wget
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import BaseDownDriverFW, Tools


class FtpDownDriver(BaseDownDriverFW):
    """
    普通ftp连接的图片下载驱动
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
        return 'ftp'

    @classmethod
    def download(cls, file_url: str, save_file: str, extend_json: dict = None, **para_dict):
        """
        下载文件
        (需继承类实现，如果下载失败应抛出异常, 正常执行完成代表下载成功)

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} extend_json=None - 要送入下载驱动的扩展信息
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
        """
        wget.download(file_url, out=save_file, bar=None)
