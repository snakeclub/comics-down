#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
aria2的下载驱动
@module aria2_down_driver
@file aria2_down_driver.py
"""
import os
import sys
import ssl
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import BaseDownDriverFW, Tools

# 取消全局ssl验证
ssl._create_default_https_context = ssl._create_unverified_context

__MOUDLE__ = 'aria2_down_driver'  # 模块名
__DESCRIPT__ = u'aria2的下载驱动'  # 模块描述
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
    def get_down_type(cls):
        """
        返回该驱动对应的下载类型
        (需继承类实现)

        @returns {str} - 下载类型字符串，如http/ftp
            注：系统加载的下载类型名不能重复
        """
        return 'aria2'

    @classmethod
    def download(cls, file_url: str, save_file: str, extend_json: dict = None, **para_dict):
        """
        下载文件
        (需继承类实现，如果下载失败应抛出异常, 正常执行完成代表下载成功)

        @param {str} file_url - 要下载的文件url
        @param {str} save_file - 要保存的文件路径及文件名
        @param {dict} extend_json=None - 要送入下载驱动的扩展信息
            headers {dict} - 要设置的http头字典
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来, 支持参数如下：
            down_overtime
            overtime
            connect_retry
            down_cookie
            down_proxy
        """
        _cmd = 'aria2c -d %s -o %s --auto-file-renaming=false --allow-overwrite=true --check-certificate=false' % (
            os.path.split(save_file)[0], os.path.split(save_file)[1],
        )

        # 补充其他参数
        _cmd = '%s -t %s --connect-timeout=%s -m %s' % (
            _cmd, para_dict.get('down_overtime', '300'),
            para_dict.get('overtime', '30'),
            para_dict.get('connect_retry', '3')
        )

        # 设置header
        if extend_json is not None:
            for _key, _val in extend_json.get('headers', {}).items():
                _cmd = '%s --header="%s: %s"' % (_cmd, _key, _val)

        # 设置cookie
        if para_dict.get('down_cookie', '') != '':
            _cookies = Tools.get_cookie_from_file(para_dict['down_cookie'])
            _cookie_str_list = list()
            for _key, _val in _cookies:
                _cookie_str_list.append('%s=%s' % (_key, _val))

            _cmd = '%s --header="%s: %s"' % (_cmd, 'Cookie', '; '.join(_cookie_str_list))

        # 设置代理
        _proxy = {}
        if para_dict.get('down_proxy', '') != '':
            _proxy = Tools.get_proxy(para_dict['down_proxy'])
            if len(_proxy) == 1:
                _key = list(_proxy.keys())[0]
                _cmd = '%s all-proxy="%s"' % (_cmd, _proxy[_key])
            else:
                for _key, _val in _proxy.items:
                    _cmd = '%s %s-proxy="%s"' % (_cmd, _key.lower(), _val)

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
