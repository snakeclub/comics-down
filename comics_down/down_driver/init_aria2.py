#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
初始化的文件下载驱动
@module init_aria2
@file init_aria2.py
"""
import os
import sys
import ssl
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.down_driver_fw import BaseDownDriverFW

# 取消全局ssl验证
ssl._create_default_https_context = ssl._create_unverified_context

__MOUDLE__ = 'init_aria2'  # 模块名
__DESCRIPT__ = u'初始化的文件下载驱动'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.03.03'  # 发布日期


class Aria2Driver(BaseDownDriverFW):
    """
    使用aria2的下载驱动(需安装aria2，并将aria2c.exe的目录加入path环境变量)
    """
    #############################
    # 需实现类继承的方法
    #############################
    @classmethod
    def get_supports(cls):
        """
        返回该驱动支持的类型

        @return {str} - 支持的类型字符串，如http
        """
        return 'aria2'

    @classmethod
    def download(cls, file_url: str, save_file: str, **para_dict):
        """
        下载文件

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
        """
        _cmd = 'aria2c.exe -d %s -o %s --auto-file-renaming=false --allow-overwrite=true --check-certificate=false' % (
            os.path.split(save_file)[0], os.path.split(save_file)[1],
        )

        # 补充其他参数
        _cmd = '%s -t %s --connect-timeout=%s -m %s' % (
            _cmd, para_dict.get('down_overtime', '300'),
            para_dict.get('overtime', '30'),
            para_dict.get('connect_retry', '3')
        )

        _cmd = '%s %s' % (_cmd, file_url)
        _ret = os.system(_cmd)
        if _ret != 0:
            raise RuntimeError('download error!')


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))

    _para_dict = {
        'url': '',
        'name': '',
        'path': '',
        'job_worker': '1',
        'auto_redo': 'n',
        'encoding': 'utf-8',
        'force_update': 'n',
        'job_down_worker': '10',
        'down_overtime': '300',
        'use_break_down': 'y',
        'overtime': '30',
        'connect_retry': '3',
        'verify': 'y',
        'remove_wget_tmp': 'y',
        'webdriver': 'Chrome',
        'wd_wait_all_loaded': 'n',
        'wd_overtime': '30',
        'wd_headless': 'n',
        'search_mode': 'n',
        'show_rate': 'n'
    }

    Aria2Driver.download(
        'http://chh.tebrobot.cn/py/images/wx.png', 'd:\\1.png', **_para_dict
    )
