#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
网站下载的驱动框架
@module driver_fw
@file driver_fw.py
"""

import os
import sys
import uuid
import time
import traceback
from HiveNetLib.simple_i18n import _
from HiveNetLib.base_tools.net_tool import EnumWebDriverType
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.down_tool import DownTool

__MOUDLE__ = 'driver_fw'  # 模块名
__DESCRIPT__ = u'网站下载的驱动框架'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.02.29'  # 发布日期


class BaseDriverFW(object):
    """
    网站下载驱动框架类
    """
    #############################
    # 工具类函数
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
    # 公共方法
    #############################
    @classmethod
    def get_id(cls):
        """
        返回该驱动的唯一标识
        (使用uuid生成随机标识，如果需要特定标识可以在实现类中重定义)

        @return {str} - 类的唯一标识
        """
        return str(uuid.uuid1())

    @classmethod
    def update_vol_info(cls, xml_doc, **para_dict):
        """
        解析网页获取并更新下载配置文件的卷信息

        @param {SimpleXml} xml_doc - 下载配置文件的操作对象
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
            关键参数包括:
            url - 漫画所在目录索引页面的url
            name - 漫画任务名
            auto_redo - 是否失败自动重做(y/n)
            encoding - 网页编码，默认为'utf-8'

        @return {bool} - 更新结果
        """
        # 通过循环支持持续执行
        while True:
            _url = ''
            try:
                # 更新卷信息及文件信息处理为未完成
                xml_doc.set_value('/down_task/info/vol_info_ok', 'n')
                xml_doc.set_value('/down_task/info/file_info_ok', 'n')
                xml_doc.save(pretty_print=True)

                _url = para_dict['url']
                _vol_next_url = ''
                if not (para_dict['search_mode'] == 'y'):
                    # 如果是搜索模式，从头开始找卷信息
                    _vol_next_url = xml_doc.get_value('/down_task/info/vol_next_url')

                if _vol_next_url is not None and _vol_next_url != '':
                    _url = _vol_next_url

                # 循环获取索引页面并更新下载配置文件
                while True:
                    _vol_info = cls._get_vol_info(_url, **para_dict)
                    for _vol in _vol_info[1].keys():
                        _vol_name = DownTool.path_char_replace(_vol)
                        _vol_url = _vol_info[1][_vol]

                        # 判断卷是否已经处理过
                        _vol_num_dict = xml_doc.get_value('/down_task/info/vol_num_dict')
                        if _vol_num_dict == '':
                            _vol_num_dict = dict()
                        else:
                            _vol_num_dict = eval(_vol_num_dict)

                        if _vol_name in _vol_num_dict.keys():
                            # 卷已经存在
                            if not (para_dict['search_mode'] == 'y'):
                                # 非搜索模式，无需处理
                                continue
                            else:
                                # 将卷信息重新打开为listing
                                xml_doc.set_value(
                                    '/down_task/down_list/%s/status' % _vol_num_dict[_vol_name],
                                    'listing'
                                )
                                xml_doc.save(pretty_print=True)
                        else:
                            DownTool.add_vol_to_down_task_conf(
                                xml_doc, _vol_name, _vol_url, status='listing'
                            )

                    # 保存下一页信息
                    xml_doc.set_value('/down_task/info/vol_next_url', _vol_info[0])
                    xml_doc.save(pretty_print=True)

                    # 检查是否有下一个url
                    if _vol_info[0] != '':
                        _url = _vol_info[0]
                        continue
                    else:
                        # 没有下一页, 退出循环
                        break

                # 正常执行下来，更新卷信息处理完成的标记
                xml_doc.set_value('/down_task/info/vol_info_ok', 'y')
                xml_doc.save()
                return True
            except:
                print('%s[%s][%s]:\n%s' % (
                    _('Get vol info error'), para_dict['name'], _url,
                    traceback.format_exc()
                ))
                if para_dict['auto_redo'] == 'y':
                    time.sleep(0.01)
                    continue
                else:
                    return False

    @classmethod
    def update_file_info(cls, xml_doc, **para_dict):
        """
        解析网页获取并更新下载配置文件的文件信息

        @param {SimpleXml} xml_doc - 下载配置文件的操作对象
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
            关键参数包括:
            auto_redo - 是否失败自动重做(y/n)
            encoding - 网页编码，默认为'utf-8'

        @return {bool} - 更新结果
        """
        # 一开始就要获取文件数量
        _files = int(xml_doc.get_value('/down_task/info/files'))

        # 通过循环支持持续执行
        while True:
            _vol_url = ''
            _vol_name = ''
            _last_tran_para = None
            try:
                # 更新文件信息处理为未完成
                xml_doc.set_value('/down_task/info/file_info_ok', 'n')
                xml_doc.save(pretty_print=True)

                # 遍历所有卷，发现未完成的进行处理
                _vol_num_dict = xml_doc.get_value('/down_task/info/vol_num_dict')
                if _vol_num_dict == '':
                    _vol_num_dict = dict()
                else:
                    _vol_num_dict = eval(_vol_num_dict)

                for _vol_name in _vol_num_dict.keys():
                    _vol_num = _vol_num_dict[_vol_name]
                    if xml_doc.get_value('/down_task/down_list/%s/status' % _vol_num) != 'listing':
                        # 已经处理完成
                        continue

                    # 按卷url解析获取下载文件清单
                    _vol_url = xml_doc.get_value('/down_task/down_list/%s/url' % _vol_num)
                    _file_info = cls._get_file_info(
                        _vol_url, _last_tran_para, **para_dict
                    )
                    if len(_file_info[1]) == 0:
                        raise RuntimeError(_('Get file info error: no file found!'))

                    # 将下载文件清单加入配置
                    _file_num = int(xml_doc.get_value(
                        '/down_task/down_list/%s/file_num' % _vol_num))
                    _file_add_num = 0
                    for _file in _file_info[1].keys():
                        # 检查文件url是否已经存在
                        _file_exist = False
                        _real_file_name = 'file_%d' % _file_num

                        if para_dict['search_mode'] == 'y':
                            # 搜索模式，从所有文件url判断
                            if xml_doc.get_value("//url[text()='%s']" % _file_info[1][_file][0]) != '':
                                # 找到文件已存在
                                _file_exist = True
                        else:
                            # 非搜索模式，仅判断当前卷
                            if xml_doc.get_value("/down_task/down_list/%s/files/%s/url[text()='%s']" % (_vol_num, _real_file_name, _file_info[1][_file][0])) != '':
                                # 找到文件已存在
                                _file_exist = True

                        if not _file_exist:
                            # 文件不存在，新增
                            _file_num += 1
                            _file_add_num += 1
                            DownTool.add_file_to_down_task_conf(
                                xml_doc, _vol_num, _real_file_name,
                                DownTool.path_char_replace(_file),
                                _file_info[1][_file][0],
                                _file_info[1][_file][1],
                            )

                    # 更新_last_tran_para
                    _last_tran_para = _file_info[0]

                    # 处理完更新卷状态及文件总数
                    xml_doc.set_value('/down_task/down_list/%s/file_num' % _vol_num, str(_file_num))
                    xml_doc.set_value('/down_task/down_list/%s/status' % _vol_num, 'downloading')
                    _files += _file_add_num
                    xml_doc.set_value('/down_task/info/files', str(_files))
                    xml_doc.save(pretty_print=True)

                # 全部文件清单处理完成
                xml_doc.set_value('/down_task/info/files', str(_files))
                xml_doc.set_value('/down_task/info/file_info_ok', 'y')
                xml_doc.save(pretty_print=True)
                return True
            except:
                print('%s[%s][%s][%s]:\n%s' % (
                    _('Get file info error'), para_dict['name'], _vol_name, _vol_url,
                    traceback.format_exc()
                ))
                if para_dict['auto_redo'] == 'y':
                    time.sleep(0.01)
                    continue
                else:
                    return False

    #############################
    # 需实现类继承的方法
    #############################
    @classmethod
    def get_supports(cls):
        """
        返回该驱动支持的网站清单
        (需继承类实现)

        @return {dict} - 支持的清单:
            key - 网站域名
            value - 网站说明
        """
        raise NotImplementedError()

    @classmethod
    def get_name_by_url(cls, **para_dict):
        """
        根据url获取下载漫画名
        (需继承类实现)

        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
            关键参数包括:
            url - 漫画所在目录索引页面的url

        @return {str} - 漫画名
        """
        raise NotImplementedError()

    @classmethod
    def _get_vol_info(cls, index_url: str, **para_dict):
        """
        获取漫画的卷列表信息
        (需继承类实现)

        @param {str} index_url - 漫画所在目录索引的url
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来

        @return {list} - 卷信息数组
            [0] - vol_next_url，传入下一页的url，如果没有下一页，传空
            [1] - 卷信息字典(dict), key为卷名，value为浏览该卷漫画的url
            注：
            (1)应用会根据vol_next_url判断要不要循环获取卷信息
            (2)卷名可以通过标签‘{$path_split$}’来设置卷保存的子目录
        """
        raise NotImplementedError()

    @classmethod
    def _get_file_info(cls, vol_url: str, last_tran_para: object, **para_dict):
        """
        获取对应卷的下载文件清单

        @param {str} vol_url - 浏览该卷漫画的url
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来

        @return {list} - 返回文件清单
            [0] - 要传入下一次执行的参数对象（实现类自定义）
            [1] - 下载文件信息字典(dict), key为文件名，value为文件信息数组:
                [文件url, 下载类型]
            注：目前下载类型支持http、ftp
        """
        raise NotImplementedError


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))
