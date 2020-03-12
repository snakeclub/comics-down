#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
独特类型文件的下载驱动框架
@module down_driver_fw
@file down_driver_fw.py
"""
import os
import sys
import uuid
from HiveNetLib.base_tools.net_tool import EnumWebDriverType
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))

__MOUDLE__ = 'down_driver_fw'  # 模块名
__DESCRIPT__ = u'独特类型文件的下载驱动框架'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.03.03'  # 发布日期


class BaseDownDriverFW(object):
    """
    文件下载驱动框架
    """
    #############################
    # 公共方法
    #############################
    @classmethod
    def get_webdriver_type(cls, typestr: str):
        """
        根据字符串获取webdriver的类型

        @param {str} typestr - 类型字符串

        @return {EnumWebDriverType} - 枚举类型
        """
        return EnumWebDriverType(typestr)

    #############################
    # 需实现类继承的方法
    #############################
    @classmethod
    def get_supports(cls):
        """
        返回该驱动支持的类型
        (需继承类实现)

        @return {str} - 支持的类型字符串，如http
        """
        raise NotImplementedError()

    @classmethod
    def download(cls, file_url: str, save_file: str, **para_dict):
        """
        下载文件
        (需继承类实现，如果下载失败应抛出异常)

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
        """
        raise NotImplementedError()


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))
