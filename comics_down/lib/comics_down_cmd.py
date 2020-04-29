#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
comics-down工具命令模块
@module comics_down_cmd
@file comics_down_cmd.py
"""

import os
import sys
import traceback
import time
import copy
import inspect
from urllib.parse import urlparse
try:
    import chardet
except:
    pass
from HiveNetLib.base_tools.run_tool import RunTool
from HiveNetLib.base_tools.import_tool import ImportTool
from HiveNetLib.base_tools.exception_tool import ExceptionTool
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.simple_i18n import _
from HiveNetLib.simple_console.base_cmd import CmdBaseFW
from HiveNetLib.generic import CResult
from HiveNetLib.simple_xml import SimpleXml
from HiveNetLib.simple_queue import MemoryQueue
from HiveNetLib.simple_parallel import ParallelPool, ThreadParallel, ThreadParallelLock, ThreadParallelShareDict
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.down_tool import DownTool
from comics_down.lib.driver_fw import BaseDriverFW
from comics_down.lib.down_driver_fw import BaseDownDriverFW


__MOUDLE__ = 'mediawiki_cmd'  # 模块名
__DESCRIPT__ = u'mediawiki工具命令模块'  # 模块描述
__VERSION__ = '0.5.1'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2019.12.09'  # 发布日期


class ComicsDownCmd(CmdBaseFW):
    """
    comics-down的处理命令
    """
    #############################
    # 工具类函数
    #############################
    @classmethod
    def import_drivers(cls, path: str):
        """
        加载网站下载驱动

        @param {str} path - 要加载驱动的路径

        @return {bool} - 加载结果
        """
        _path = os.path.realpath(path)
        if not os.path.exists(_path):
            print(_("Import drivers error, path '$1' not exists!", _path))
            return False

        # 全局变量中存储加载字典
        _driver_dict = RunTool.get_global_var('DRIVER_DICT')
        if _driver_dict is None:
            _driver_dict = {
                'site_route': dict(),  # 网站域名对应到类ID的的路由字典
                'class': dict(),  # 类ID与类对象的对应字典，类ID由实现类提供
                'website': dict(),  # 支持的网页清单介绍
            }
            RunTool.set_global_var('DRIVER_DICT', _driver_dict)

        # 遍历文件执行加载
        _file_list = FileTool.get_filelist(path=_path, regex_str=r'.*\.py$', is_fullname=False)
        for _file in _file_list:
            if _file == '__init__.py':
                continue

            # 执行加载
            _module = ImportTool.import_module(_file[0: -3], extend_path=_path, is_force=True)
            _clsmembers = inspect.getmembers(_module, inspect.isclass)
            for (_class_name, _class) in _clsmembers:
                if not hasattr(_class, 'get_supports') or _class == BaseDriverFW:
                    # 通过get_supports来判断是否驱动类
                    continue

                # 类对象加入到字典中
                _class_id = _class.get_id()
                _driver_dict['class'][_class_id] = _class

                # 增加支持的网站路由
                _support_list = _class.get_supports()
                for _website in _support_list:
                    _driver_dict['site_route'][_website.upper()] = _class_id  # 网站与类id对应
                    _driver_dict['website'][_website] = _support_list[_website]  # 网站说明

        # 完成处理
        return True

    @classmethod
    def import_down_drivers(cls, path: str):
        """
        加载文件下载驱动

        @param {str} path - 要加载驱动的路径

        @return {bool} - 加载结果
        """
        _path = os.path.realpath(path)
        if not os.path.exists(_path):
            print(_("Import down drivers error, path '$1' not exists!", _path))
            return False

        # 全局变量中存储加载字典
        _driver_dict = RunTool.get_global_var('DOWN_DRIVER_DICT')
        if _driver_dict is None:
            _driver_dict = dict()  # key为类型，value为类对象
            RunTool.set_global_var('DOWN_DRIVER_DICT', _driver_dict)

        # 遍历文件执行加载
        _file_list = FileTool.get_filelist(path=_path, regex_str=r'.*\.py$', is_fullname=False)
        for _file in _file_list:
            if _file == '__init__.py':
                continue

            # 执行加载
            _module = ImportTool.import_module(_file[0: -3], extend_path=_path, is_force=True)
            _clsmembers = inspect.getmembers(_module, inspect.isclass)
            for (_class_name, _class) in _clsmembers:
                if not hasattr(_class, 'get_supports') or _class == BaseDownDriverFW:
                    # 通过get_supports来判断是否驱动类
                    continue

                # 类对象加入到字典中
                _driver_dict[_class.get_supports()] = _class

        # 完成处理
        return True

    #############################
    # 构造函数，在里面增加函数映射字典
    #############################

    def _init(self, **kwargs):
        """
        实现类需要覆盖实现的初始化函数

        @param {kwargs} - 传入初始化参数字典（config.xml的init_para字典）

        @throws {exception-type} - 如果初始化异常应抛出异常
        """
        self._CMD_DEALFUN_DICT = {
            'set_driver_path': self._set_driver_path_cmd_dealfun,
            'support': self._support_cmd_dealfun,
            'set_default_save_path': self._set_default_save_path_cmd_dealfun,
            'download': self._download_cmd_dealfun,
            'set_down_driver_path': self._set_down_driver_path_cmd_dealfun
        }
        self._console_global_para = RunTool.get_global_var('CONSOLE_GLOBAL_PARA')

        # 从配置获取其他信息
        _config_xml = SimpleXml(
            self._console_global_para['config_file'],
            encoding=self._console_global_para['config_encoding']
        )
        _driver_path = _config_xml.get_value('/console/driver_path')
        if _driver_path != '':
            _driver_path = os.path.realpath(
                os.path.join(
                    os.path.realpath(self._console_global_para['execute_file_path']),
                    _config_xml.get_value('/console/driver_path')
                )
            )
        self._console_global_para['driver_path'] = _driver_path
        self._console_global_para['default_save_path'] = _config_xml.get_value(
            '/console/default_save_path')

        # 装载默认网站驱动
        self.import_drivers(
            os.path.join(self._console_global_para['execute_file_path'], 'driver')
        )

        # 装载自定义的网站驱动
        if _driver_path != '':
            self.import_drivers(_driver_path)

        self.driver_dict = RunTool.get_global_var('DRIVER_DICT')

        # 装载默认文件下载驱动
        self.import_down_drivers(
            os.path.join(self._console_global_para['execute_file_path'], 'down_driver')
        )

        # 装载自定义的文件下载驱动
        _down_driver_path = _config_xml.get_value('/console/down_driver_path')
        if _down_driver_path != '':
            _down_driver_path = os.path.realpath(
                os.path.join(
                    os.path.realpath(self._console_global_para['execute_file_path']),
                    _down_driver_path
                )
            )
            self.import_down_drivers(_down_driver_path)

        self.down_driver_dict = RunTool.get_global_var('DOWN_DRIVER_DICT')

        # 下载需要的公共变量
        self.job_queue = MemoryQueue()

    #############################
    # 实际处理函数
    #############################

    def _cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        通用处理函数，通过cmd区别调用实际的处理函数

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取真实执行的函数
        self._prompt_obj = prompt_obj  # 传递到对象内部处理
        _real_dealfun = None  # 真实调用的函数
        if 'ignore_case' in kwargs.keys() and kwargs['ignore_case']:
            # 区分大小写
            if cmd in self._CMD_DEALFUN_DICT.keys():
                _real_dealfun = self._CMD_DEALFUN_DICT[cmd]
        else:
            # 不区分大小写
            if cmd.lower() in self._CMD_DEALFUN_DICT.keys():
                _real_dealfun = self._CMD_DEALFUN_DICT[cmd.lower()]

        # 执行函数
        if _real_dealfun is not None:
            return _real_dealfun(message=message, cmd=cmd, cmd_para=cmd_para, prompt_obj=prompt_obj, **kwargs)
        else:
            prompt_obj.prompt_print(_("'$1' is not support command!", cmd))
            return CResult(code='11404', i18n_msg_paras=(cmd, ))

    #############################
    # 实际处理函数
    #############################
    def _set_driver_path_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        设置网站下载驱动的搜索路径

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        _result = CResult(code='00000')

        _path = cmd_para.strip()
        if _path == '':
            prompt_obj.prompt_print(_('path must be not null'))
            return _result

        self._console_global_para['driver_path'] = os.path.realpath(_path)
        if not os.path.exists(self._console_global_para['driver_path']):
            prompt_obj.prompt_print(
                _("Path '$1' not exists!", self._console_global_para['driver_path'])
            )
            return _result

        # 修改配置文件中的驱动搜索路径
        _config_xml = SimpleXml(
            self._console_global_para['config_file'],
            encoding=self._console_global_para['config_encoding']
        )
        _config_xml.set_value(
            '/console/driver_path',
            _path
        )
        _config_xml.save()

        # 加载支持的网站
        self.import_drivers(self._console_global_para['driver_path'])

        prompt_obj.prompt_print(_("Driver path set to '$1'",
                                  self._console_global_para['driver_path']))

        # 结束
        return _result

    def _set_down_driver_path_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        设置下载驱动的搜索路径

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        _result = CResult(code='00000')

        _path = cmd_para.strip()
        if _path == '':
            prompt_obj.prompt_print(_('path must be not null'))
            return _result

        self._console_global_para['down_driver_path'] = os.path.realpath(_path)
        if not os.path.exists(self._console_global_para['down_driver_path']):
            prompt_obj.prompt_print(
                _("Path '$1' not exists!", self._console_global_para['down_driver_path'])
            )
            return _result

        # 修改配置文件中的驱动搜索路径
        _config_xml = SimpleXml(
            self._console_global_para['config_file'],
            encoding=self._console_global_para['config_encoding']
        )
        _config_xml.set_value(
            '/console/down_driver_path',
            _path
        )
        _config_xml.save()

        # 加载支持的下载驱动
        self.import_down_drivers(self._console_global_para['down_driver_path'])

        prompt_obj.prompt_print(_("Down driver path set to '$1'",
                                  self._console_global_para['down_driver_path']))

        # 结束
        return _result

    def _set_default_save_path_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        设置默认的下载保存目录

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        _result = CResult(code='00000')

        _path = cmd_para.strip()
        if _path == '':
            prompt_obj.prompt_print(_('path must be not null'))
            return _result

        self._console_global_para['default_save_path'] = os.path.realpath(_path)
        if not os.path.exists(self._console_global_para['default_save_path']):
            # 创建目录
            FileTool.create_dir(self._console_global_para['default_save_path'])

        # 修改配置文件中的默认保存目录
        _config_xml = SimpleXml(
            self._console_global_para['config_file'],
            encoding=self._console_global_para['config_encoding']
        )
        _config_xml.set_value(
            '/console/default_save_path',
            _path
        )
        _config_xml.save()

        prompt_obj.prompt_print(_("Default save path set to '$1'",
                                  self._console_global_para['default_save_path']))

        # 结束
        return _result

    def _support_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        显示支持的网站列表

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        prompt_obj.prompt_print(_('support website list') + ":\n")
        _driver_dict = RunTool.get_global_var('DRIVER_DICT')
        for _website in _driver_dict['website'].keys():
            prompt_obj.prompt_print('%s : %s\n' % (_website, _driver_dict['website'][_website]))

        return CResult(code='00000')

    def _download_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        执行下载处理

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取字典参数
        _para_dict = self._cmd_para_to_dict(cmd_para, name_with_sign=False)

        # 默认保存目录
        _default_save_path = self._console_global_para['default_save_path']
        if _default_save_path == '':
            _default_save_path = self._console_global_para['work_path']

        _para_dict.setdefault('path', _default_save_path)

        # 通过参数启动任务
        return self._start_download(para_dict=_para_dict, prompt_obj=prompt_obj, **kwargs)

    #############################
    # 内部函数
    #############################
    def _start_download(self, para_dict: dict, prompt_obj=None, **kwargs):
        """
        启动下载任务

        @param {dict} para_dict - 参数字典
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示

        @returns {CResult} - 下载结果
        """
        _result = CResult(code='00000')
        _job_result = dict()
        RunTool.set_global_var('JOB_RESULT', _job_result)

        with ExceptionTool.ignored_cresult(
            result_obj=_result, self_log_msg=_('Download get exception'), debug=True
        ):
            if 'job_file' in para_dict.keys():
                # 从文件中获取url列表执行下载, 通过并行方式下载
                _bytes = None
                with open(para_dict['job_file'], 'rb') as _file:
                    _bytes = _file.read()

                # 判断字符集
                _file_encoding = 'utf-8'
                try:
                    _file_encoding = chardet.detect(_bytes)['encoding']
                    if _file_encoding.startswith('ISO-8859'):
                        _file_encoding = 'gbk'
                except:
                    pass

                # 放入队列中
                self.job_queue.clear()
                _job_list = str(_bytes, encoding=_file_encoding).replace('\r', '\n').split('\n')
                for _job in _job_list:
                    _job = _job.strip()
                    if _job != '':
                        self.job_queue.put([_job, para_dict, prompt_obj, kwargs])

                # 启动线程池执行下载处理
                _pool = ParallelPool(
                    deal_fun=self._down_job_worker_fun,
                    parallel_class=ThreadParallel,
                    run_args=(self.job_queue, ),
                    task_queue=self.job_queue,
                    maxsize=int(para_dict.get('job_worker', '1')),
                    sharedict_class=ThreadParallelShareDict,
                    parallel_lock_class=ThreadParallelLock,
                    auto_stop=True
                )
                # 启动线程池
                _pool.start()

                # 等待任务结束
                while not _pool.is_stop:
                    time.sleep(1)
            else:
                # 单url下载
                self._download_job_start(para_dict, prompt_obj=prompt_obj, **kwargs)

        # 显示执行结果
        prompt_obj.prompt_print('%s : \n' % _('Download finished'))
        for _name in _job_result.keys():
            _info = _job_result[_name]
            prompt_obj.prompt_print(
                'Task [%s] %s: files[%d] success[%d] task[%d] task_fail[%d] msg[%s]' % (
                    _name, _info['status'], _info['files'],
                    _info['success'], _info['task'], _info['task_fail'], _info['msg']
                )
            )

        return _result

    def _download_job_start(self, para_dict: dict, prompt_obj=None, **kwargs):
        """
        执行下载任务

        @param {dict} para_dict - 下载参数字典
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        """
        _result = CResult(code='00000')
        _down_info = {
            'status': 'downloading',
            'msg': '',
            'files': 0,
            'success': 0,
            'task': 0,
            'task_fail': 0
        }

        # 处理默认的配置信息
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
            'wd_min': 'n',
            'search_mode': 'n',
            'show_rate': 'n'
        }
        _para_dict.update(para_dict)

        with ExceptionTool.ignored_cresult(
            result_obj=_result, self_log_msg=_('Download job exception'), debug=True
        ):
            _driver = None
            _url_info = None

            # 获取任务名
            if _para_dict['name'] == '':
                if _para_dict['url'] == '':
                    _down_info['msg'] = _('url or name must at least set one!')
                    raise AssertionError(_down_info['msg'])

                _url_info = urlparse(_para_dict['url'])
                _site = _url_info.netloc.upper()
                if _site not in self.driver_dict['site_route'].keys():
                    _down_info['msg'] = _('not driver for the website [$1]', _site)
                    raise RuntimeError(_down_info['msg'])

                _driver = self.driver_dict['class'][self.driver_dict['site_route'][_site]]
                _para_dict['name'] = _driver.get_name_by_url(**_para_dict)

            # 确保漫画名能作为目录保存
            _para_dict['name'] = DownTool.path_char_replace(_para_dict['name'])

            # 加入到结果清单
            RunTool.get_global_var('JOB_RESULT')[_para_dict['name']] = _down_info

            # 获取配置文件
            _xml_doc = DownTool.get_down_task_conf(
                _para_dict['path'], _para_dict['name'], _para_dict['url']
            )
            # 更新一些信息到内存
            if _para_dict['url'] == '':
                _para_dict['url'] = _xml_doc.get_value('/down_task/info/url')
            _down_info['files'] = int(_xml_doc.get_value('/down_task/info/files'))
            _down_info['success'] = int(_xml_doc.get_value('/down_task/info/success'))
            _vol_info_ok = _xml_doc.get_value('/down_task/info/vol_info_ok')
            _file_info_ok = _xml_doc.get_value('/down_task/info/file_info_ok')

            # 判断驱动是否为空，如果为空有可能是因为传了name进来
            if _driver is None:
                _url_info = urlparse(_para_dict['url'])
                _site = _url_info.netloc.upper()
                if _site not in self.driver_dict['site_route'].keys():
                    _down_info['msg'] = _('not driver for the website [$1]', _site)
                    raise RuntimeError(_down_info['msg'])

                _driver = self.driver_dict['class'][self.driver_dict['site_route'][_site]]

            # 解析网页获取卷信息 - 在驱动框架已处理了自动重试
            if _para_dict['force_update'] == 'y' or _para_dict['search_mode'] == 'y' or _vol_info_ok != 'y':
                if not _driver.update_vol_info(_xml_doc, **_para_dict):
                    _down_info['msg'] = _('Update vol info error')
                    raise RuntimeError(_down_info['msg'])

            # 解析网页获取每个卷的文件
            if _para_dict['force_update'] == 'y' or _para_dict['search_mode'] == 'y' or _file_info_ok != 'y':
                if not _driver.update_file_info(_xml_doc, **_para_dict):
                    _down_info['msg'] = _('Update files info error')
                    raise RuntimeError(_down_info['msg'])

            # 循环处理下载任务, 在有失败的情况重新执行
            while True:
                try:
                    # 重置信息
                    _down_info['task'] = 0
                    _down_info['task_fail'] = 0
                    _down_info['msg'] = ''

                    # 执行下载
                    _downtool = DownTool(_xml_doc, **_para_dict)
                    _downtool.start_down_file()

                    # 正常执行完成，检查是否已完成
                    if _para_dict['auto_redo'] == 'y' and _down_info['task_fail'] > 0:
                        time.sleep(0.01)
                        continue

                    # 退出处理
                    break
                except:
                    print('%s[%s]:\n%s' % (
                        _('start downlong file error'), _para_dict['name'],
                        traceback.format_exc()
                    ))
                    if _para_dict['auto_redo'] == 'y':
                        time.sleep(0.01)
                        continue
                    else:
                        _down_info['msg'] = _('start downlong file error')
                        raise RuntimeError(_down_info['msg'])

        # 处理返回
        if not _result.is_success():
            _down_info['status'] = 'error'
            if _down_info['msg'] == '':
                _down_info['msg'] = _result.msg

            if _para_dict['name'] == '':
                if _para_dict['url'] == '':
                    RunTool.get_global_var('JOB_RESULT')['null'] = _down_info
                else:
                    RunTool.get_global_var('JOB_RESULT')[_para_dict['url']] = _down_info

    def _down_job_worker_fun(self, q, ):
        """
        下载任务工作函数
        """
        try:
            _job = q.get(block=False)
            _para_dict = copy.deepcopy(_job[1])
            _job_infos = _job[0].split('|')
            _para_dict['url'] = _job_infos[0]
            if len(_job_infos) > 1:
                _para_dict['name'] = _job_infos[1]
            self._download_job_start(_para_dict, prompt_obj=_job[2], **_job[3])
        except:
            # 没有取到任务
            time.sleep(1)
            return None


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))
