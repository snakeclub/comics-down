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

import json
import os
import subprocess
import sys
import traceback
from urllib.parse import urlparse
from HiveNetLib.base_tools.run_tool import RunTool
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.simple_i18n import _
from HiveNetLib.simple_console.base_cmd import CmdBaseFW
from HiveNetLib.generic import CResult
from HiveNetLib.simple_xml import SimpleXml
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import DriverManager, JobManager, Tools
from comics_down.lib.auto_analyse import AnalyzeTool


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
    # 构造函数，在里面增加函数映射字典
    #############################

    def _init(self, **kwargs):
        """
        实现类需要覆盖实现的初始化函数

        @param {kwargs} - 传入初始化参数字典（config.xml的init_para字典）

        @throws {exception-type} - 如果初始化异常应抛出异常
        """
        self._CMD_DEALFUN_DICT = {
            'set_website_driver_path': self._set_website_driver_path_cmd_dealfun,
            'set_down_driver_path': self._set_down_driver_path_cmd_dealfun,
            'set_default_save_path': self._set_default_save_path_cmd_dealfun,
            'support': self._support_cmd_dealfun,
            'download': self._download_cmd_dealfun,
            'get_down_index': self._get_down_index_cmd_dealfun,
            'show_down_index': self._show_down_index_cmd_dealfun,
            'start_proxy_server': self._start_proxy_server_cmd_dealfun,
            'stop_proxy_server': self._stop_proxy_server_cmd_dealfun,
            'analysis_video_urls': self._analysis_video_urls_cmd_dealfun,
            'download_file': self._download_file_cmd_dealfun,
            'download_webpage_video': self._download_webpage_video_cmd_dealfun,
            'analysis_xpath': self._analysis_xpath_cmd_dealfun
        }
        self._console_global_para = RunTool.get_global_var('CONSOLE_GLOBAL_PARA')

        # 从配置获取其他信息
        _config_xml = SimpleXml(
            self._console_global_para['config_file'],
            encoding=self._console_global_para['config_encoding']
        )
        # 私有驱动目录
        self._console_global_para['website_driver_path'] = _config_xml.get_value(
            '/console/website_driver_path')
        self._console_global_para['down_driver_path'] = _config_xml.get_value(
            '/console/down_driver_path')
        # 默认保存路径
        self._console_global_para['default_save_path'] = _config_xml.get_value(
            '/console/default_save_path')
        # 默认shell编码
        self._console_global_para['shell_encoding'] = _config_xml.get_value(
            '/console/shell_encoding')
        # python命令
        self._console_global_para['python_cmd'] = _config_xml.get_value(
            '/console/python_cmd')

        # 默认下载映射转换字典
        self._console_global_para['downtype_mapping'] = _config_xml.get_value(
            '/console/downtype_mapping')
        self._console_global_para['common_wd_overwrite'] = (
            _config_xml.get_value('/console/common_wd_overwrite') == 'true'
        )

    def _init_after_console_init(self):
        """
        实现类需要覆盖实现的simple_console初始化后要执行的函数
        """
        self._console_global_para = RunTool.get_global_var('CONSOLE_GLOBAL_PARA')

        # 设置命令行打印工具
        RunTool.set_global_var(
            'CONSOLE_PRINT_FUNCTION', self._console_global_para['prompt_obj'].prompt_print
        )

        # 装载驱动
        _downtype_mapping = {}
        if self._console_global_para['downtype_mapping'] != '':
            _downtype_mapping = json.loads(self._console_global_para['downtype_mapping'])

        DriverManager.init_drivers(
            self._console_global_para['execute_file_path'],
            private_website_driver=self._console_global_para['website_driver_path'],
            private_down_driver=self._console_global_para['down_driver_path'],
            default_downtype_mapping=_downtype_mapping,
            common_wd_overwrite=self._console_global_para['common_wd_overwrite']
        )

        # 初始化任务管理器
        self._console_global_para['job_manager'] = JobManager(
            self._console_global_para['execute_file_path'],
            python_cmd=self._console_global_para['python_cmd'],
            shell_encoding=self._console_global_para['shell_encoding']
        )

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
    def _set_website_driver_path_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
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

        _real_path = os.path.join(
            self._console_global_para['execute_file_path'], _path
        )

        if not os.path.exists(_real_path):
            prompt_obj.prompt_print(
                _("Path '$1' not exists!", _real_path)
            )
            return _result

        # 加载网站驱动
        if not DriverManager.import_website_drivers(_real_path):
            # 加载失败
            return _result

        # 设置私有驱动参数
        self._console_global_para['website_driver_path'] = _path

        _config_xml = SimpleXml(
            self._console_global_para['config_file'],
            encoding=self._console_global_para['config_encoding']
        )
        _config_xml.set_value(
            '/console/website_driver_path',
            _path
        )
        _config_xml.save()

        prompt_obj.prompt_print(
            _("Driver path set to '$1'", self._console_global_para['website_driver_path'])
        )

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

        _real_path = os.path.join(
            self._console_global_para['execute_file_path'], _path
        )

        if not os.path.exists(_real_path):
            prompt_obj.prompt_print(_("Path '$1' not exists!", _real_path))
            return _result

        # 加载下载驱动
        DriverManager.import_down_drivers(_real_path)

        # 设置私有驱动参数
        self._console_global_para['down_driver_path'] = _path

        _config_xml = SimpleXml(
            self._console_global_para['config_file'],
            encoding=self._console_global_para['config_encoding']
        )
        _config_xml.set_value(
            '/console/down_driver_path',
            _path
        )
        _config_xml.save()

        prompt_obj.prompt_print(
            _("Down driver path set to '$1'", self._console_global_para['down_driver_path'])
        )

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

        prompt_obj.prompt_print(
            _("Default save path set to '$1'",
              self._console_global_para['default_save_path'])
        )

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
        _websites = DriverManager.get_supported_website()
        for _host, _note in _websites.items():
            prompt_obj.prompt_print('%s : %s\n' % (_host, _note))

        return CResult(code='00000')

    def _download_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        执行下载处理

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象
            shell_cmd {bool} - 如果传入参数有该key，且值为True，代表是命令行直接执行，非进入控制台执行

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
        _para_dict['path'] = os.path.realpath(_para_dict['path'])

        # 根据参数启动下载任务
        _job_manager: JobManager = self._console_global_para['job_manager']
        try:
            _sub_process = (_para_dict.get('sub_process', 'n') == 'y')
            _asyn = True
            if kwargs.get('shell_cmd', False):
                # 命令行进入的方式，要同步完成
                _asyn = False

            _ret = _job_manager.start_job(
                'download', _para_dict, sub_process=_sub_process, asyn=_asyn
            )
            if type(_ret) == dict:
                prompt_obj.prompt_print('%s : \n' % _('Download finished'))
                prompt_obj.prompt_print(
                    'Task [%s] %s: files[%d] success[%d] task[%d] task_fail[%d] msg[%s]' % (
                        _ret['name'], _ret['status'], _ret['files'],
                        _ret['success'], _ret['task'], _ret['task_fail'], _ret['msg']
                    )
                )
                if _ret['status'] != 'done':
                    return CResult(code='29999')
        except:
            _result = CResult(code='29999', msg=traceback.format_exc())
            _result.print_str = _result.msg
            return _result

        return CResult(code="00000")

    def _get_down_index_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        获取资源下载索引文件

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象
            shell_cmd {bool} - 如果传入参数有该key，且值为True，代表是命令行直接执行，非进入控制台执行

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
        _para_dict['path'] = os.path.realpath(_para_dict['path'])

        # 根据参数启动下载任务
        _job_manager: JobManager = self._console_global_para['job_manager']
        try:
            _sub_process = (_para_dict.get('sub_process', 'n') == 'y')
            _asyn = True
            if kwargs.get('shell_cmd', False):
                # 命令行进入的方式，要同步完成
                _asyn = False

            _ret = _job_manager.start_job(
                'index', _para_dict, sub_process=_sub_process, asyn=_asyn
            )
            if type(_ret) == dict:
                prompt_obj.prompt_print('%s : \n' % _('Get download index finished'))
                prompt_obj.prompt_print(
                    'Task [%s] %s: files[%d] success[%d] task[%d] task_fail[%d] msg[%s]' % (
                        _ret['name'], _ret['status'], _ret['files'],
                        _ret['success'], _ret['task'], _ret['task_fail'], _ret['msg']
                    )
                )
        except:
            _result = CResult(code='29999', msg=traceback.format_exc())
            _result.print_str = _result.msg
            return _result

        return CResult(code="00000")

    def _show_down_index_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        获取资源下载索引文件

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象
            shell_cmd {bool} - 如果传入参数有该key，且值为True，代表是命令行直接执行，非进入控制台执行

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
        _para_dict['path'] = os.path.realpath(_para_dict['path'])

        # 根据参数启动下载任务
        _job_manager: JobManager = self._console_global_para['job_manager']
        try:
            _infos = _job_manager.get_down_index_info(_para_dict['name'], _para_dict['path'])
            _type = _para_dict.get('type', 'info')
            if _type == 'vols':
                # 显示卷信息
                for _vol_num, _vol_info in _infos['down_list'].items():
                    prompt_obj.prompt_print(
                        'vol_num[%s] name[%s] status[%s] files[%s] url[%s]' % (
                            _vol_num, _vol_info['name'], _vol_info['status'],
                            _vol_info['file_num'], _vol_info['url']
                        )
                    )
            elif _type == 'files':
                # 显示文件清单
                _vol_num = _para_dict.get('vol_num', '')
                if _vol_num == '':
                    _vols = list(_infos['down_list'].keys())
                else:
                    _vols = [_vol_num]

                # 遍历卷展示
                for _vol_num in _vols:
                    _vol_info = _infos['down_list'][_vol_num]
                    prompt_obj.prompt_print(
                        'vol_num[%s] name[%s] status[%s] files[%s] url[%s]' % (
                            _vol_num, _vol_info['name'], _vol_info['status'],
                            _vol_info['file_num'], _vol_info['url']
                        )
                    )
                    for _file_num in _vol_info['files'].keys():
                        _file_info = _vol_info['files'][_file_num]
                        prompt_obj.prompt_print(
                            'name[%s] status[%s] downtype[%s] url[%s]' % (
                                _file_info['name'], _file_info['status'], _file_info['downtype'],
                                _file_info['url']
                            )
                        )

                    prompt_obj.prompt_print('')  # 换行
            else:
                # 显示基础信息
                prompt_obj.prompt_print(
                    'name:[%s] status[%s] files[%s] success[%s] url[%s]' % (
                        _infos['info']['name'], _infos['info']['status'], _infos['info']['files'],
                        _infos['info']['success'], _infos['info']['url']
                    )
                )
        except:
            _result = CResult(code='29999', msg=traceback.format_exc())
            _result.print_str = _result.msg
            return _result

        return CResult(code="00000")

    def _start_proxy_server_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        启动代理服务

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象
            shell_cmd {bool} - 如果传入参数有该key，且值为True，代表是命令行直接执行，非进入控制台执行

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取字典参数
        _para_dict = self._cmd_para_to_dict(cmd_para, name_with_sign=False)
        _base_path = self._console_global_para['execute_file_path']
        try:
            _proxy_dict = RunTool.get_global_var('RUNNING_PROXY_DICT')
            if _proxy_dict is None:
                _proxy_dict = dict()
                RunTool.set_global_var('RUNNING_PROXY_DICT', _proxy_dict)

            # 判断是否已启动
            if _para_dict['proxy'] in _proxy_dict.keys():
                prompt_obj.prompt_print('proxy [%s] already running!' % _para_dict['proxy'])
                return CResult(code="00000")

            # 启动命令
            _cmd = 'mitmdump -s %s -p %s' % (
                os.path.join(_base_path, _para_dict['proxy']),
                _para_dict.get('port', '9000')
            )

            # 运行
            if sys.platform == 'win32':
                # windows，创建新窗口执行
                _sp = subprocess.Popen(
                    _cmd, close_fds=True, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                _sp = subprocess.Popen(_cmd, close_fds=True, shell=True)

            _proxy_dict[_para_dict['proxy']] = _sp
            prompt_obj.prompt_print('start proxy server success')
        except:
            _result = CResult(code='29999', msg=traceback.format_exc())
            _result.print_str = _result.msg
            return _result

        return CResult(code="00000")

    def _stop_proxy_server_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        停止代理服务

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象
            shell_cmd {bool} - 如果传入参数有该key，且值为True，代表是命令行直接执行，非进入控制台执行

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取字典参数
        _para_dict = self._cmd_para_to_dict(cmd_para, name_with_sign=False)
        try:
            _proxy_dict = RunTool.get_global_var('RUNNING_PROXY_DICT')
            if _proxy_dict is None:
                _proxy_dict = dict()
                RunTool.set_global_var('RUNNING_PROXY_DICT', _proxy_dict)

            # 判断是否已启动
            if _para_dict['proxy'] not in _proxy_dict.keys():
                prompt_obj.prompt_print('proxy [%s] not running!' % _para_dict['proxy'])
                return CResult(code="00000")

            _proxy_dict[_para_dict['proxy']].kill()
            _proxy_dict.pop(_para_dict['proxy'], None)
            prompt_obj.prompt_print('stop proxy server success')
        except:
            _result = CResult(code='29999', msg=traceback.format_exc())
            _result.print_str = _result.msg
            return _result

        return CResult(code="00000")

    def _analysis_video_urls_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        解析指定页面的视频地址

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象
            shell_cmd {bool} - 如果传入参数有该key，且值为True，代表是命令行直接执行，非进入控制台执行

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取字典参数
        _para_dict = self._cmd_para_to_dict(cmd_para, name_with_sign=False)

        _url = _para_dict.pop('url', '')
        if _url == '':
            prompt_obj.prompt_print(_('url must be not null'))
            return CResult(code="29999")

        _extends = _para_dict.pop('extends', ['m3u8', 'mp4'])

        try:
            _urls = AnalyzeTool.get_media_url(
                _url, type_list=_extends, back_all=True, **_para_dict
            )
            prompt_obj.prompt_print('\n'.join(_urls))
        except:
            _result = CResult(code='29999', msg=traceback.format_exc())
            _result.print_str = _result.msg
            return _result

        return CResult(code="00000")

    def _download_file_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        解析指定页面的视频地址

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象
            shell_cmd {bool} - 如果传入参数有该key，且值为True，代表是命令行直接执行，非进入控制台执行

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取字典参数
        _para_dict = self._cmd_para_to_dict(cmd_para, name_with_sign=False)

        _url = _para_dict.get('url', '')
        if _url == '':
            prompt_obj.prompt_print(_('url must be not null'))
            return CResult(code="29999")

        _save_file = _para_dict.pop('save_file', '')
        if _save_file == '':
            prompt_obj.prompt_print(_('save_file must be not null'))
            return CResult(code="29999")

        _save_file = os.path.join(
            self._console_global_para['work_path'], _save_file
        )

        _extend_json = _para_dict.pop('extend_json', None)
        if _extend_json is not None:
            _extend_json = json.loads(_extend_json)

        try:
            _down_driver = DriverManager.get_down_driver(
                _para_dict.pop('downtype', 'http'),
                json.loads(_para_dict.get('downtype_mapping', '{}'))
            )
            _down_driver.download(_url, _save_file, extend_json=_extend_json, **_para_dict)
            prompt_obj.prompt_print(_('Download finished'))
        except:
            _result = CResult(code='29999', msg=traceback.format_exc())
            _result.print_str = _result.msg
            return _result

        return CResult(code="00000")

    def _download_webpage_video_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        解析指定页面并下载视频文件

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象
            shell_cmd {bool} - 如果传入参数有该key，且值为True，代表是命令行直接执行，非进入控制台执行

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取字典参数
        _para_dict = self._cmd_para_to_dict(cmd_para, name_with_sign=False)

        _url = _para_dict.pop('url', '')
        if _url == '':
            prompt_obj.prompt_print(_('url must be not null'))
            return CResult(code="29999")

        _extends = _para_dict.pop('extends', ['m3u8', 'mp4'])
        _filename = _para_dict.pop('filename', '')
        _downtype = _para_dict.pop('downtype', 'http')
        _extend_json = _para_dict.pop('extend_json', None)
        if _extend_json is not None:
            _extend_json = json.loads(_extend_json)

        # 默认保存目录
        _default_save_path = self._console_global_para['default_save_path']
        if _default_save_path == '':
            _default_save_path = self._console_global_para['work_path']

        _para_dict.setdefault('path', _default_save_path)
        _para_dict['path'] = os.path.realpath(_para_dict['path'])

        try:
            # 判断是否直接为文件下载url
            _ext = FileTool.get_file_ext(urlparse(_url).path).lower()
            if _ext not in _extends:
                # 需要解析页面获下载url
                _url = AnalyzeTool.get_media_url(
                    _url, type_list=_extends, **_para_dict
                )
                if _url is None:
                    prompt_obj.prompt_print(_('no video file found in web page'))
                    return CResult(code="29999")

                _ext = FileTool.get_file_ext(urlparse(_url).path).lower()  # 更新扩展名

            # 处理下载文件名
            if _filename == '':
                _filename = os.path.split(urlparse(_url).path)[1]
                if _ext == 'm3u8':
                    _filename = _filename[0:-4] + 'mp4'

            # 处理文件下载
            if _ext == 'm3u8':
                _downtype = 'm3u8'

            _down_driver = DriverManager.get_down_driver(
                _downtype, json.loads(_para_dict.get('downtype_mapping', '{}'))
            )
            prompt_obj.prompt_print(_('download file: $1', _url))
            _down_driver.download(
                _url, os.path.join(_para_dict['path'], _filename),
                extend_json=_extend_json, **_para_dict
            )
            prompt_obj.prompt_print(_('Download finished'))

        except:
            _result = CResult(code='29999', msg=traceback.format_exc())
            _result.print_str = _result.msg
            return _result

        return CResult(code="00000")

    def _analysis_xpath_cmd_dealfun(self, message='', cmd='', cmd_para='', prompt_obj=None, **kwargs):
        """
        解析指定元素的xpath

        @param {string} message='' - prompt提示信息
        @param {string} cmd - 执行的命令key值
        @param {string} cmd_para - 传入的命令参数（命令后的字符串，去掉第一个空格）
        @param {PromptPlus} prompt_obj=None - 传入调用函数的PromptPlus对象，可以通过该对象的一些方法控制输出显示
        @param {kwargs} - 传入的主进程的初始化kwargs对象
            shell_cmd {bool} - 如果传入参数有该key，且值为True，代表是命令行直接执行，非进入控制台执行

        @returns {CResult} - 命令执行结果，可通过返回错误码10101通知框架退出命令行, 同时也可以通过CResult对象的
            print_str属性要求框架进行打印处理
        """
        # 获取字典参数
        _para_dict = self._cmd_para_to_dict(cmd_para, name_with_sign=False)

        _url = _para_dict.pop('url', '')
        if _url == '':
            prompt_obj.prompt_print(_('url must be not null'))
            return CResult(code="29999")

        _content = _para_dict.pop('content', '')
        if _content == '':
            prompt_obj.prompt_print(_('content must be not null'))
            return CResult(code="29999")

        _use_html_code = _para_dict.pop('use_html_code', 'y')
        _attr_name = _para_dict.pop('attr_name', '')
        _is_tail = _para_dict.pop('is_tail', 'n')
        _selector_up_level = _para_dict.pop('selector_up_level', '3')
        _split_class = _para_dict.pop('split_class', 'n')

        _para_dict = Tools.get_correct_para_dict(_para_dict)

        try:
            _configs = AnalyzeTool.get_contents_config(
                [_url], check_contents={'name': [_content]}, attr_name=({} if _attr_name == '' else {'name': [_attr_name]}),
                is_tail=(_is_tail == 'y'), use_html_code=(_use_html_code == 'y'),
                search_dict={
                    'selector_up_level': _selector_up_level,
                    'split_class': (_split_class == 'y')
                },
                **_para_dict
            )
            prompt_obj.prompt_print(_configs['name'])
        except:
            _result = CResult(code='29999', msg=traceback.format_exc())
            _result.print_str = _result.msg
            return _result

        return CResult(code="00000")


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))
