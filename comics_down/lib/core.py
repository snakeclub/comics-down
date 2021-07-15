#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
下载工具模块
@module core
@file core.py
"""
import os
import sys
import time
import json
import copy
import inspect
import threading
import traceback
import subprocess
import uuid
try:
    import chardet
except:
    pass
from urllib.parse import urlparse
from HiveNetLib.simple_webdriver import EnumWebDriverType
from HiveNetLib.base_tools.run_tool import RunTool
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.base_tools.import_tool import ImportTool
from HiveNetLib.simple_i18n import _
from HiveNetLib.simple_xml import SimpleXml, EnumXmlObjType
from HiveNetLib.simple_queue import MemoryQueue
from HiveNetLib.simple_parallel import ParallelPool, ThreadParallel, ThreadParallelLock, ThreadParallelShareDict, NotRunning, CallOverTime, ProcessParallelShareDict
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))


__MOUDLE__ = 'core'  # 模块名
__DESCRIPT__ = u'框架核心模块'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.02.29'  # 发布日期


#############################
# 全局变量定义
# WEBSITE_DRIVER_DICT : 加载的网站驱动字典
#   site_route : 网站域名对应到类ID的的路由字典
#       key为支持的特定域名(转换为大写字母), value为可用的类ID列表[id1, id2, ...]
#   class : 类ID与类对象的对应字典，类ID由实现类的 get_id() 函数提供
#       key为类ID，value为类对象
#   website : 支持的网页清单介绍字典，由实现类的 get_supports() 函数提供
#       key为域名，value为网站介绍
#
# DOWN_DRIVER_DICT : 加载的下载驱动字典，key为下载类型，value为对应的下载驱动类
#############################

#############################
# 下载配置文件格式, 统一命名 down.xml
# down_task
#     info : 基本信息
#         name : 漫画名(任务名, 也是path下的漫画目录名)
#         url : 漫画所在目录索引页面的url
#         status : 整个资源下载状态, downloading, done
#         vol_info_ok : 卷清单是否已更新成功
#         file_info_ok : 文件清单是否已更新成功
#         files : 总文件数
#         success : 成功下载数
#         vol_num : 最大卷号
#         vol_num_dict : 卷名和卷id的对应关系字典字符串（json格式字符串）
#         vol_next_url : 处理卷目录时如果存在多页的情况，在一页成功后传入下一页的url
#     down_list : 下载清单
#         vol_[num] : 卷id
#             name : 卷名(也是卷目录名)
#             url : 目录对应的浏览url
#             status : 下载状态, listing-正在获取清单, downloading-正在下载, done-下载完成
#             file_num : 最大文件号
#             files : 要下载的文件清单
#                 file_[num] : 文件标识
#                     name : 文件名
#                     url : 下载的url
#                     status : 下载状态, err, done
#                     downtype : 下载类型，目前支持：http, ftp
#                     extend_json : 与下载相关的扩展json字典
#     error : 本次处理的异常信息（每次启动会删除）
#         vol_[num]
#             name : 卷名(也是卷目录名)
#             url : 目录对应的浏览url
#             files : 要下载的文件
#                 file_[num] : 文件标识
#                     name : 文件名
#                     url : 下载的url
#############################


class Tools(object):
    """
    常用工具
    """

    @classmethod
    def get_print_fun(cls):
        """
        获取打印函数
        注：尝试获取全局的打印函数，用于兼容命令行的情况，如果获取不到则采用系统自带打印函数

        @returns {object} - 返回兼容打印函数
        """
        _print = RunTool.get_global_var('CONSOLE_PRINT_FUNCTION')
        if _print is None:
            _print = print

        return _print

    @classmethod
    def get_correct_para_dict(cls, para_dict: dict) -> dict:
        """
        获取修正后的下载参数

        @param {dict} para_dict - 送入的参数

        @returns {dict} - 修正后的参数（含默认值）
        """
        _para_dict = {
            'url': '',
            'name': '',
            'path': '',
            'job_worker': '1',
            'auto_redo': '0',
            'encoding': 'utf-8',
            'force_update': 'n',
            'down_worker': '10',
            'down_overtime': '300',
            'use_break_down': 'y',
            'overtime': '30',
            'connect_retry': '3',
            'verify': 'y',
            'remove_wget_tmp': 'y',
            'website_driver_id': '',
            'website_proxy': '',
            'website_cookie': '',
            'source_index': '0',
            'webdriver': 'Chrome',
            'wd_wait_all_loaded': 'n',
            'wd_overtime': '30',
            'wd_headless': 'n',
            'wd_min': 'n',
            'wd_no_image': 'n',
            'wd_default_down_path': '',
            'search_mode': 'n',
            'show_rate': 'n',
            'downtype_mapping': '',
            'down_proxy': '',
            'down_cookie': '',
            'debug_path': ''
        }
        _para_dict.update(para_dict)
        return _para_dict

    @classmethod
    def get_webdriver_type(cls, typestr: str):
        """
        根据字符串获取webdriver（非网站驱动）的类型

        @param {str} typestr - 类型字符串

        @return {EnumWebDriverType} - 枚举类型
        """
        return EnumWebDriverType(typestr)

    @classmethod
    def save_file(cls, file: str, content: str, encoding: str = 'utf-8'):
        """
        保存错误文件

        @param {str} file - 要保存的文件路径
        @param {str} content - 要保存的内容
        @param {str} encoding='utf-8' - 文件编码
        """
        with open(file, 'w', encoding=encoding) as f:
            f.write(content)

    @classmethod
    def get_proxy(cls, proxy_str: str) -> dict:
        """
        获取代理配置字典

        @param {str} proxy_str - 代理访问配置字符串
            例如: http=http://127.0.0.1:80;https=https://127.0.0.1:443
            其中代理访问地址也支持以下3种写法：
                https://127.0.0.1:80
                127.0.0.1:80
                127.0.0.1

        @returns {dict} - 返回配置字典，{'协议': 'scheme://地址和端口'}
        """
        _proxy_dict = dict()
        _proxy_list = proxy_str.split(';')
        for _proxy in _proxy_list:
            _proxy = _proxy.strip()
            if _proxy == '':
                continue

            _info = _proxy.split('=')
            # 处理访问地址
            _url = _info[1]
            _url_info = urlparse(_url)
            if _url_info.netloc == '':
                if _url_info.scheme == '':
                    # 127.0.0.1 模式
                    _url = 'http://%s:80' % _url_info.path
                else:
                    # 127.0.0.1:80 模式
                    _url = 'http://%s:%s' % (_url_info.scheme, _url_info.path)

            _proxy_dict[_info[0]] = _url

        return _proxy_dict

    @classmethod
    def get_cookie_from_file(cls, file: str, encoding: str = 'utf-8') -> dict:
        """
        从文件中获取cookie信息字典
        注：文件格式为json

        @param {str} file - 文件名
        @param {str} encoding='utf-8' - 文件编码

        @returns {dict} - cookie字典
        """
        _cookie = None
        with open(file, 'r', encoding=encoding) as _f:
            _cookie = json.loads(_f.read())

        return _cookie

    #############################
    # 通用网站驱动配置相关函数
    #############################
    @classmethod
    def load_common_website_configs(cls) -> dict:
        """
        加载网站配置到内存

        @returns {dict} - 返回配置字典
        """
        # 获取配置JSON文件
        _configs_file = cls._common_website_config_file_path()
        if os.path.exists(_configs_file):
            with open(_configs_file, 'r', encoding='utf-8') as _f:
                _configs = json.loads(_f.read())
        else:
            # 文件不存在, 初始化，并写入配置文件
            _configs = {
                'mapping': {},  # key为网站域名（含子域名）的大写形式; value为list, 0-域名对应的配置uuid, 1-是否主域名
            }
            with open(_configs_file, 'w', encoding='utf-8') as _f:
                _f.write(json.dumps(_configs, ensure_ascii=False, indent=2))

        # 加载到内存
        RunTool.set_global_var('COMMON_WEBSITE_DRIVER_CONFIG', _configs)
        return _configs

    @classmethod
    def get_common_website_configs(cls) -> dict:
        """
        获取网站配置字典

        @returns {dict} - 配置字典
            {
                'mapping': {},  # key为网站域名（含子域名）的大写形式; value为list, 0-域名对应的配置uuid, 1-是否主域名
                '[uuid]': {
                    '[网站主域名]': {
                        'remark': '网站说明',
                        'subsite': ['子域名', '子域名', ...],
                        'configs': {}  # 网站处理配置字典
                    }
                },
                ...
            }
        """
        _configs = RunTool.get_global_var('COMMON_WEBSITE_DRIVER_CONFIG')
        if _configs is None:
            _configs = cls.load_common_website_configs()

        return _configs

    @classmethod
    def add_common_website_config(cls, file: str, over_write: bool = False, ignore_exist_error: bool = False):
        """
        添加新的网站支持配置信息到通用驱动

        @param {str} file - 要添加的配置xml文件路径（当前工作目录的相对路径）
            注：xml文件格式参考 conf/common_website_dirver 中的已实现网站配置
        @param {bool} over_write=False - 存在的情况下是否覆盖原配置
        @param {bool} ignore_exist_error=False - 忽略主域名已存在的报错
        """
        _file = os.path.join(os.getcwd(), file)
        _config = SimpleXml(
            _file, obj_type=EnumXmlObjType.File, encoding='utf-8', use_chardet=False,
            remove_blank_text=True
        ).to_dict()['driver_config']

        # 检查是否有主域名冲突的情况
        _configs = cls.get_common_website_configs()
        for _host in _config.keys():
            _old_info = _configs['mapping'].get(_host.upper(), ['', 'n'])
            if _old_info[1] == 'y':
                if over_write:
                    # 覆盖模式，删除原来的节点
                    cls.remove_common_website_config(_host, save_file=False)
                else:
                    if ignore_exist_error:
                        # 忽略报错，直接退出即可
                        return
                    else:
                        raise FileExistsError('main host [%s] is exists!' % _host)

        # 添加到字典中
        for _host, _infos in _config.items():
            _uuid = str(uuid.uuid1())
            # 修正配置信息
            for _type in _infos['configs'].keys():
                # 解析脚本
                _scripts = _infos['configs'][_type].get('scripts', None)
                if _scripts is not None:
                    for _i in range(len(_scripts)):
                        try:
                            _scripts[_i] = json.loads(_scripts[_i])
                        except:
                            print('json loads error: %s' % _scripts[_i])
                            raise

                    _infos['configs'][_type]['scripts'] = _scripts

                # 子脚本
                _sub_scripts = _infos['configs'][_type].get('sub_scripts', None)
                if _sub_scripts is None or _sub_scripts == '':
                    _infos['configs'][_type]['sub_scripts'] = {}
                else:
                    for _id in _sub_scripts.keys():
                        _scripts = _sub_scripts[_id]
                        for _i in range(len(_scripts)):
                            _scripts[_i] = json.loads(_scripts[_i])

                        _sub_scripts[_id] = _scripts

                    _infos['configs'][_type]['sub_scripts'] = _sub_scripts

            _configs[_uuid] = {
                _host.lower(): _infos
            }
            # 添加映射信息
            _configs['mapping'][_host.upper()] = [_uuid, 'y']
            _subsite = _infos.get('subsite', '[]')
            if _subsite == '':
                _subsite = []
            else:
                _subsite = json.loads(_subsite)

            _infos['subsite'] = _subsite

            for _site in _subsite:
                _configs['mapping'][_site.upper()] = [_uuid, 'n']

        # 保存到配置文件
        _configs_file = cls._common_website_config_file_path()
        with open(_configs_file, 'w', encoding='utf-8') as _f:
            _f.write(json.dumps(_configs, ensure_ascii=False, indent=2))

    @classmethod
    def remove_common_website_config(cls, host: str, save_file: bool = True):
        """
        删除指定的主域名配置

        @param {str} host - 主域名
        @param {bool} save_file=True - 是否保存到配置文件
        """
        _host = host.upper()
        _configs = cls.get_common_website_configs()
        if _host not in _configs['mapping'].keys() or _configs['mapping'][_host][1] != 'y':
            raise FileNotFoundError('main host [%s] is not exists!' % host)

        # 删除配置
        _uuid = _configs['mapping'][_host][0]
        _site_list = list(_configs['mapping'].keys())
        for _site in _site_list:
            if _configs['mapping'][_site][0] == _uuid:
                _configs['mapping'].pop(_site, None)

        _configs.pop(_uuid, None)

        # 保存到配置文件
        if save_file:
            _configs_file = cls._common_website_config_file_path()
            with open(_configs_file, 'w', encoding='utf-8') as _f:
                _f.write(json.dumps(_configs, ensure_ascii=False, indent=2))

    #############################
    # 内部函数
    #############################

    @classmethod
    def _common_website_config_file_path(cls) -> str:
        """
        返回配置文件路径

        @returns {str} - 配置文件路径
        """
        _console_global_para = RunTool.get_global_var('CONSOLE_GLOBAL_PARA')
        if _console_global_para is None:
            # 没有在命令行模式启动，通过自身路径找到配置
            _execute_file_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), os.path.pardir)
            )
        else:
            _execute_file_path = _console_global_para['execute_file_path']

        # 获取配置JSON文件
        return os.path.join(_execute_file_path, 'conf/common_website_driver.json')


class DriverManager(object):
    """
    控件管理类
    """

    @classmethod
    def init_drivers(cls, base_path: str, private_website_driver: str = '', private_down_driver: str = '',
                     default_downtype_mapping: dict = {}, common_wd_overwrite: bool = False):
        """
        初始化驱动的加载

        @param {str} base_path - 基础目录（程序所在目录）
        @param {str} private_website_driver - 私有网站驱动目录
        @param {str} private_down_driver - 私有下载驱动目录
        @param {dict} default_downtype_mapping - 默认的下载类型与下载驱动对应关系映射字典
        @param {bool} common_wd_overwrite - 启动时是否自动重新装载驱动
        """
        # 加载默认驱动
        cls.import_website_drivers(
            os.path.join(base_path, 'website_driver')
        )
        cls.import_down_drivers(
            os.path.join(base_path, 'down_driver')
        )

        # 加载私有驱动
        if private_website_driver != '':
            cls.import_website_drivers(
                os.path.join(base_path, private_website_driver)
            )
        if private_down_driver != '':
            cls.import_down_drivers(
                os.path.join(base_path, private_down_driver)
            )

        # 自动加载通用网站驱动配置
        _files = FileTool.get_filelist(
            path=os.path.join(base_path, 'conf/common_website_dirver'),
            regex_str=r'.*\.xml$'
        )
        for _file in _files:
            Tools.add_common_website_config(
                _file, over_write=common_wd_overwrite, ignore_exist_error=True
            )

        # 更新全局默认映射关系变量, 确保m3u8文件可以正常被处理
        _downtype_mapping = {'m3u8': 'm3u8'}
        _downtype_mapping.update(default_downtype_mapping)
        RunTool.set_global_var('DEFAULT_DOWNTYPE_MAPPING_DICT', _downtype_mapping)

    @classmethod
    def import_website_drivers(cls, path: str):
        """
        加载网站下载驱动

        @param {str} path - 要加载驱动的路径

        @return {bool} - 加载结果
        """
        _print = Tools.get_print_fun()
        _path = os.path.realpath(path)
        if not os.path.exists(_path):
            _print(_("Import website drivers error, path '$1' not exists!", _path))
            return False

        # 全局变量中存储加载字典
        _driver_dict = RunTool.get_global_var('WEBSITE_DRIVER_DICT')
        if _driver_dict is None:
            _driver_dict = {
                'site_route': dict(),  # 网站域名对应到类ID的的路由字典
                'class': dict(),  # 类ID与类对象的对应字典，类ID由实现类提供
                'website': dict(),  # 支持的网页清单介绍
            }
            RunTool.set_global_var('WEBSITE_DRIVER_DICT', _driver_dict)

        # 遍历文件执行加载
        _file_list = FileTool.get_filelist(path=_path, regex_str=r'.*\.py$', is_fullname=False)
        for _file in _file_list:
            if _file == '__init__.py':
                continue

            # 执行加载
            _module = ImportTool.import_module(_file[0: -3], extend_path=_path, is_force=True)
            _clsmembers = inspect.getmembers(_module, inspect.isclass)
            for (_class_name, _class) in _clsmembers:
                if not hasattr(_class, 'get_supports') or _class == BaseWebSiteDriverFW:
                    # 通过get_supports来判断是否驱动类
                    continue

                # 类对象加入到字典中
                _class_id = _class.get_id()
                _driver_dict['class'][_class_id] = _class

                # 增加支持的网站路由
                _support_list = _class.get_supports()
                for _website, _site_infos in _support_list.items():
                    _subsite = _site_infos.get('subsite', [])
                    _subsite.append(_website)  # 把主网站也放到清单里
                    for _host in _subsite:
                        _host = _host.upper()
                        if _host in _driver_dict['site_route'].keys():
                            # 添加新的id，并且排序在前面
                            try:
                                _driver_dict['site_route'][_host].remove(_class_id)  # 可能以前添加过
                            except:
                                pass
                            _driver_dict['site_route'][_host].insert(0, _class_id)  # 放到最前面
                        else:
                            # 添加网站支持
                            _driver_dict['site_route'][_host] = [_class_id, ]  # 网站与类id对应

                    _driver_dict['website'][_website] = '%s[%s]' % (
                        _site_infos.get('remark', ''), ', '.join(_subsite)
                    )  # 网站说明，增加子域名显示

        # 完成处理
        return True

    @classmethod
    def import_down_drivers(cls, path: str):
        """
        加载文件下载驱动

        @param {str} path - 要加载驱动的路径

        @return {bool} - 加载结果
        """
        _print = Tools.get_print_fun()
        _path = os.path.realpath(path)
        if not os.path.exists(_path):
            _print(_("Import down drivers error, path '$1' not exists!", _path))
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
                if not hasattr(_class, 'get_down_type') or _class == BaseDownDriverFW:
                    # 通过get_down_type来判断是否驱动类
                    continue

                # 类对象加入到字典中
                _driver_dict[_class.get_down_type()] = _class

        # 完成处理
        return True

    @classmethod
    def get_supported_website(cls) -> dict:
        """
        获取驱动支持的网站清单

        @returns {dict} - 驱动支持的网站清单，key为网站域名，value为介绍
        """
        _website_driver_dict = RunTool.get_global_var('WEBSITE_DRIVER_DICT', default={})
        return _website_driver_dict.get('website', {})

    @classmethod
    def get_website_driver(cls, url: str = '', class_id: str = ''):
        """
        获取匹配的网站驱动类

        @param {str} url='' - url地址
        @param {str} class_id='' - 指定的类id

        @returns {BaseWebSiteDriverFW} - 匹配上的类对象
        """
        _driver_dict = RunTool.get_global_var('WEBSITE_DRIVER_DICT', {})
        if class_id != '':
            # 优先通过id指定获取
            _class = _driver_dict.get('class', {}).get(class_id, None)
            if _class is None:
                raise RuntimeError(_('not website driver with id [$1]', class_id))
        else:
            # 通过url获取网站驱动
            _url_info = urlparse(url)
            _host = _url_info.netloc.upper()
            _class_id = _driver_dict.get('site_route', {}).get(_host, None)
            if _class_id is None or len(_class_id) == 0:
                raise RuntimeError(_('not website driver for the website [$1]', _host))

            _class = _driver_dict.get('class', {}).get(_class_id[0], None)  # 取排序第一个

        # 返回结果
        return _class

    @classmethod
    def get_down_driver(cls, downtype: str, downtype_mapping: dict):
        """
        获取指定的下载驱动类

        @param {str} downtype - 下载类型
        @param {dict} downtype_mapping - 下载驱动映射字典

        @returns {BaseDownDriverFW} - 下载驱动类对象
        """
        _downtype = downtype
        # 通过默认映射，以及外部送入的映射关系，变更映射字典
        _downtype_mapping = {}
        _downtype_mapping.update(RunTool.get_global_var('DEFAULT_DOWNTYPE_MAPPING_DICT', {}))
        _downtype_mapping.update(downtype_mapping)

        if downtype in _downtype_mapping.keys():
            _downtype = _downtype_mapping[downtype]
        elif '*' in _downtype_mapping.keys():
            # 支持通配符的指定方式
            _downtype = _downtype_mapping['*']

        _down_driver_dict = RunTool.get_global_var('DOWN_DRIVER_DICT')
        if _downtype not in _down_driver_dict.keys():
            raise RuntimeError(_('not support downtype [$1]', _downtype))

        return _down_driver_dict[_downtype]


class DownloadManager(object):
    """
    下载管理器（下载已完成资源下载清单获取的内容）
    """
    #############################
    # 静态方法
    #############################
    @staticmethod
    def path_char_replace(path: str, replace_str='_'):
        """
        将目录中的特殊字符进行替换（解决特殊字符做不了目录的问题）
        """
        _char_list = ['*', '|', ':', '?', '/', '<', '>', '"', ' ', "'", "\\", '-']
        _new_path = path
        for i in _char_list:
            if i in _new_path:
                _new_path = _new_path.replace(i, replace_str)
        return _new_path

    @staticmethod
    def get_down_task_conf(path: str, name, url=''):
        """
        创建或获取下载配置文件信息

        @param {str} path - 保存目录, 不含漫画名(漫画目录)
        @param {str} name - 漫画名(实际的漫画目录名)
        @param {string} url='' - 漫画所在目录索引的url

        @return {SimpleXml} - 返回配置文件
        """
        _path = os.path.realpath(os.path.join(path, name))
        _conf_file = os.path.join(_path, 'down.xml')
        _xml_doc = None
        if os.path.exists(_conf_file):
            # 配置文件已存在，直接获取
            _xml_doc = SimpleXml(
                _conf_file, obj_type=EnumXmlObjType.File,
                encoding='utf-8', use_chardet=False,
                remove_blank_text=True
            )
        else:
            # 配置不存在，新增配置文件
            _xml_str = u"""
            <down_task>
            </down_task>
            """

            _xml_doc = SimpleXml(
                _xml_str, obj_type=EnumXmlObjType.String, encoding='utf-8', use_chardet=False,
                remove_blank_text=True
            )
            _xml_doc.set_value('/down_task/info/name', name)
            _xml_doc.set_value('/down_task/info/url', url)
            _xml_doc.set_value('/down_task/info/status', 'downloading')
            _xml_doc.set_value('/down_task/info/vol_info_ok', 'n')
            _xml_doc.set_value('/down_task/info/file_info_ok', 'n')
            _xml_doc.set_value('/down_task/info/files', '0')
            _xml_doc.set_value('/down_task/info/success', '0')
            _xml_doc.set_value('/down_task/info/vol_num', '0')
            _xml_doc.set_value('/down_task/info/vol_num_dict', '{}')
            _xml_doc.set_value('/down_task/info/vol_next_url', '')

            # 保存文件
            if not os.path.exists(_path):
                FileTool.create_dir(_path, exist_ok=True)

            _xml_doc.save(
                file=_conf_file, encoding='utf-8', pretty_print=True
            )

            # 重新加载
            _xml_doc = SimpleXml(
                _conf_file, obj_type=EnumXmlObjType.File,
                encoding='utf-8', use_chardet=False,
                remove_blank_text=True
            )

        # 返回获取到的配置文件对象
        return _xml_doc

    @staticmethod
    def add_vol_to_down_task_conf(xml_doc: SimpleXml, vol_name: str, url: str, status='listing'):
        """
        将卷信息加入到任务配置文件

        @param {SimpleXml} xml_doc - 配置文件对象
        @param {str} vol_name - 卷名
        @param {str} url - 浏览该卷漫画的url
        @param {str} status='listing' - 状态

        @return {str} - 返回配置中的卷标识（vol_num）
        """
        # 获取卷标识, 并将卷最大数字+1
        _current_vol_num = int(xml_doc.get_value('/down_task/info/vol_num'))
        _vol_num = 'vol_%d' % _current_vol_num
        _current_vol_num += 1
        xml_doc.set_value('/down_task/info/vol_num', str(_current_vol_num))

        # 设置卷配置
        _xpath = '/down_task/down_list/%s' % _vol_num
        xml_doc.set_value('%s/name' % _xpath, vol_name)
        xml_doc.set_value('%s/url' % _xpath, url)
        xml_doc.set_value('%s/status' % _xpath, status)
        xml_doc.set_value('%s/file_num' % _xpath, '0')

        # 设置字典映射关系
        _vol_num_dict = json.loads(xml_doc.get_value('/down_task/info/vol_num_dict', default='{}'))

        _vol_num_dict[vol_name] = _vol_num
        xml_doc.set_value(
            '/down_task/info/vol_num_dict',
            json.dumps(_vol_num_dict, ensure_ascii=False)
        )

        # 保存
        xml_doc.save(pretty_print=True)

        # 返回处理结果
        return _vol_num

    @staticmethod
    def add_file_to_down_task_conf(xml_doc: SimpleXml, vol_num: str, file_num: str,
                                   file_name: str, url: str, downtype: str, extend_json: dict = None):
        """
        将文件信息加入到任务配置文件（注意该方法不保存配置）

        @param {SimpleXml} xml_doc - 配置文件对象
        @param {str} vol_num - 卷标识
        @param {str} file_num - 文件标识
        @param {str} file_name - 文件名
        @param {str} url - 下载url
        @param {str} downtype - 下载类型
        @param {dict} extend_json=None - 要送入下载驱动的扩展信息
        """
        _xpath = '/down_task/down_list/%s/files/%s' % (vol_num, file_num)
        xml_doc.set_value('%s/name' % _xpath, file_name)
        xml_doc.set_value('%s/url' % _xpath, url)
        xml_doc.set_value('%s/status' % _xpath, '')
        xml_doc.set_value('%s/downtype' % _xpath, downtype)
        if extend_json is not None:
            xml_doc.set_value(
                '%s/extend_json' % _xpath, json.dumps(extend_json, ensure_ascii=False)
            )

    #############################
    # 需要初始化处理的方法
    #############################
    def __init__(self, xml_doc, **para_dict):
        """
        构造函数

        @param {SimpleXml} xml_doc - 下载配置文件的操作对象
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
        """
        # 尝试获取全局的打印函数，用于兼容命令行的情况，如果获取不到则采用系统自带打印函数
        self.print = RunTool.get_global_var('CONSOLE_PRINT_FUNCTION')
        if self.print is None:
            self.print = print

        # 参数处理
        self.xml_doc = xml_doc
        self.para_dict = para_dict
        _downtype_mapping = para_dict.get('downtype_mapping', '{}')
        if _downtype_mapping == '':
            _downtype_mapping = '{}'
        self.downtype_mapping = json.loads(_downtype_mapping)
        self.lock = threading.RLock()  # 更新下载清单配置文件的锁对象
        self.pool: ParallelPool = None  # 并发池对象
        self.listing_vol = 0  # 没有正确获取到文件清单的卷数

        self.down_vol_info = dict()  # 用于登记每个卷下载图片数的字典
        self.down_queue = MemoryQueue()  # 下载下载任务的队列
        self.down_info = {
            'name': '',  # 漫画名
            'status': 'downloading',  # 状态包括 downloading-正在下载,done-完成下载, error-出现异常
            'msg': '',  # 失败的错误信息
            'files': 0,  # 总文件数
            'success': 0,  # 下载成功数
            'task': 0,  # 本次处理任务数
            'task_fail': 0  # 本次处理任务失败数
        }  # 下载信息

        self.down_driver_dict = RunTool.get_global_var('DOWN_DRIVER_DICT')

    def start_download(self):
        """
        启动下载文件处理
        """
        # 启动任务时重新获取所有文件数量
        self.down_info.update({
            'status': 'downloading',
            'msg': '',
            'files': 0,
            'success': 0,
            'task': 0,
            'task_fail': 0
        })
        self.down_info['name'] = self.xml_doc.get_value('/down_task/info/name')
        self.down_info['files'] = int(self.xml_doc.get_value('/down_task/info/files'))
        self.down_info['success'] = int(self.xml_doc.get_value('/down_task/info/success'))

        # 将下载任务放入队列
        self._add_down_task_to_queue()

        # 检查下载队列情况
        if not self._check_down_status():
            # 没有待下载数据
            return

        # 创建进程池
        self.pool = ParallelPool(
            deal_fun=self._down_worker_fun,
            parallel_class=ThreadParallel,
            run_args=(self.down_queue, ),
            task_queue=self.down_queue,
            maxsize=int(self.para_dict['down_worker']),
            worker_overtime=float(self.para_dict['down_overtime']),
            replace_overtime_worker=True,
            sharedict_class=ThreadParallelShareDict,
            parallel_lock_class=ThreadParallelLock,
            auto_stop=True
        )
        # 启动线程池
        self.pool.start()

        # 等待任务结束
        while not self.pool.is_stop:
            time.sleep(1)

        # 再次检查任务
        self._check_down_status()

    def stop_download(self, overtime=10, force=False):
        """
        停止下载处理

        @param {int} overtime=10 - 等待超时时间，单位为秒，超过时间抛出异常
        @param {bool} force=False - 是否强制关闭并发池，直接中止所有任务

        @returns {bool} - 停止结果，True-成功，False-停止失败，超时返回
        """
        if self.pool is None:
            return True

        try:
            self.pool.stop(overtime=overtime, force=force)
        except NotRunning:
            # 本来就没有运行
            return True
        except CallOverTime:
            # 停止超时
            return False

    #############################
    # 内部函数
    #############################

    def _check_down_status(self):
        """
        检查当前下载情况并判断是否要更新下载状态
        """
        if self.down_queue.empty():
            # 已经没有下载文件了，先更新数据
            self.xml_doc.set_value('/down_task/info/success', str(self.down_info['success']))

            if self.down_info['files'] == self.down_info['success'] and self.listing_vol == 0:
                # 任务已完成
                self.down_info['status'] = 'done'
                self.xml_doc.set_value('/down_task/info/status', 'done')

                # 看是否删除wget临时文件
                if self.para_dict['remove_wget_tmp'] == 'y':
                    self._remove_wget_tmp()
            else:
                # 任务未完成且数据不对
                self.down_info['status'] = 'error'
                self.down_info['msg'] = _('no files for download, but job not done!')

            # 保存
            self.xml_doc.save(pretty_print=True)
            return False
        else:
            return True

    def _remove_wget_tmp(self):
        """
        删除wget下载失败时的临时文件
        """
        FileTool.remove_all_with_path(
            path=os.path.join(self.para_dict['path'], self.para_dict['name']),
            regex_str=r'^.*\.(TMP|tmp)$',
            with_sub_path=True
        )

    def _add_down_task_to_queue(self):
        """
        将下载任务放入队列
        """
        # 清除队列
        self.down_queue.clear()
        self.down_vol_info.clear()
        self.listing_vol = 0

        # 遍历所有卷加入下载任务
        _vol_num_dict = self.xml_doc.get_value('/down_task/info/vol_num_dict')
        if _vol_num_dict == '':
            _vol_num_dict = dict()
        else:
            _vol_num_dict = eval(_vol_num_dict)

        for _vol_name in _vol_num_dict.keys():
            _vol_num = _vol_num_dict[_vol_name]
            _vol_status = self.xml_doc.get_value('/down_task/down_list/%s/status' % _vol_num)

            if _vol_status == 'listing':
                # 文件清单没有完成处理
                self.listing_vol += 1
                continue

            elif _vol_status == 'done':
                # 已完成，不处理
                continue

            _file_list = self.xml_doc.to_dict('/down_task/down_list/%s/files' % _vol_num)['files']
            if type(_file_list) == str:
                # 没有要下载的文件
                continue

            self.down_vol_info[_vol_num] = {
                'down': 0,
                'success': 0
            }

            # 添加文件到队列
            for _file in _file_list.keys():
                if _file_list[_file]['status'] == 'done':
                    continue

                # 0-卷id，1-文件id，2-卷名，3-文件名，4-文件下载url，5-下载类型, 6-下载扩展json字符串
                _file_name = _file_list[_file]['name']
                self.down_queue.put([
                    _vol_num, _file, _vol_name, _file_name,
                    _file_list[_file]['url'], _file_list[_file]['downtype'],
                    _file_list[_file].get('extend_json', '')
                ])

                # 添加到任务统计
                self.down_info['task'] += 1

                # 添加到卷的统计信息中
                self.down_vol_info[_vol_num]['down'] += 1

            # 再次判断一下是否全部完成
            if self.down_vol_info[_vol_num]['down'] == 0:
                self.xml_doc.set_value('/down_task/down_list/%s/status' % _vol_num, 'done')
                self.xml_doc.save(pretty_print=True)

    def _down_worker_fun(self, q, ):
        """
        下载工作函数
        """
        # 0-卷id，1-文件id，2-卷名，3-文件名，4-文件下载url，5-下载类型, 6-下载扩展json字符串
        _task = None
        _url = ''

        try:
            _task = q.get(block=False)
        except:
            # 没有取到任务
            time.sleep(1)
            return None

        try:
            _url = _task[4]
            _file_name = _task[3]
            if _file_name == '':
                _file_name = os.path.split(_url)[1]

            _save_file = os.path.join(
                self.para_dict['path'], self.para_dict['name'], _task[2].replace(
                    '{$path_split$}', '/'), _file_name
            )
            _save_path = os.path.split(_save_file)[0]
            if os.path.exists(_save_file) and os.path.isfile(_save_file):
                FileTool.remove_file(_save_file)

            if not os.path.exists(_save_path):
                FileTool.create_dir(_save_path, exist_ok=True)

            # 执行下载
            _down_class = DriverManager.get_down_driver(
                _task[5], self.downtype_mapping
            )
            _extend_json = None
            if _task[6] != '':
                _extend_json = json.loads(_task[6])
            _down_class.download(
                _url, _save_file, extend_json=_extend_json, **self.para_dict
            )

            # 下载成功，更新下载结果
            self.lock.acquire()
            try:
                self.xml_doc.set_value(
                    '/down_task/down_list/%s/files/%s/status' % (_task[0], _task[1]),
                    'done', debug=True
                )
                self.down_info['success'] += 1
                self.down_vol_info[_task[0]]['success'] += 1
                self.xml_doc.set_value(
                    '/down_task/info/success',
                    str(self.down_info['success']), debug=True
                )
                self.xml_doc.save(pretty_print=True)

                if self.down_vol_info[_task[0]]['success'] == self.down_vol_info[_task[0]]['down']:
                    # 当前卷下载任务已经处理完成
                    self.xml_doc.set_value(
                        '/down_task/down_list/%s/status' % _task[0],
                        'done', debug=True
                    )
                    self.xml_doc.save(pretty_print=True)
            finally:
                self.lock.release()

            self.print(
                '%s[%s -> %s -> %s]: %s' % (
                    _('DownLoad Sucess'),
                    self.para_dict['name'], _task[0], _task[1], _url
                )
            )
            time.sleep(1)
            return True
        except:
            # 下载失败
            self.print(traceback.format_exc())
            self.lock.acquire()
            try:
                self.down_info['task_fail'] += 1
                self.xml_doc.set_value(
                    '/down_task/down_list/%s/files/%s/status' % (_task[0], _task[1]),
                    'err'
                )
                self.xml_doc.set_value(
                    '/down_task/error/%s/files/%s/url' % (_task[0], _task[1]),
                    _url, debug=True
                )
                self.xml_doc.save(pretty_print=True)
            except:
                self.print('%s:\n%s' % (_('Update down config file error'), traceback.format_exc()))
            finally:
                self.lock.release()

            self.print(
                '%s[%s -> %s -> %s]: %s\n%s' % (
                    _('Download Failed'), self.para_dict['name'],
                    _task[0], _task[1], _url, traceback.format_exc()
                )
            )
            time.sleep(1)
            return False


class JobManager(object):
    """
    下载任务管理器
    """

    def __init__(self, execute_path: str, python_cmd: str = 'python', shell_encoding: str = 'utf-8'):
        """
        下载任务管理器

        @param {str} execute_path - 执行程序目录
        @param {str} python_cmd='python' - python执行命令
        @param {str} shell_encoding='utf-8' - 终端编码
        """
        # 基础参数
        self.print = Tools.get_print_fun()
        self.execute_cmd = '%s %s' % (
            python_cmd,
            os.path.realpath(
                os.path.join(execute_path, 'console.py')
            )
        )
        self.shell_encoding = shell_encoding

        # 正在运行的任务，key为job_id，value为dict
        #     key为任务id
        #       name : 任务名
        #       path : 任务所在路径
        #       popen : 任务的Pipe对象
        self.running_jobs = dict()
        # 等待执行的任务，key为job_id，value为MemoryQueue
        self.job_queues = dict()
        # 任务的执行参数，key为job_id，value为job_worker限制
        self.job_worker_num = dict()
        # 启动任务监控线程
        self._monitor_stop = False
        self._monitor_thread = threading.Thread(
            target=self._monitor_thread_fun
        )
        self._monitor_thread.setDaemon(True)
        self._monitor_thread.start()

    def __del__(self):
        """
        析构函数，删除监控线程
        """
        self._monitor_stop = True

    #############################
    # 静态函数
    #############################
    @classmethod
    def get_down_index_status(cls, name: str, path: str) -> dict:
        """
        获取下载索引文件的状态信息

        @param {str} name - 下载漫画名
        @param {str} path - 保存路径

        @returns {dict} - 状态信息字典
            {
                'name': '漫画名',
                'url': '访问路径',
                'status', '状态',
                'files': '总文件数',
                'success': '下载成功数'
            }
        """
        _status = dict()
        _conf_file = os.path.join(path, name, 'down.xml')
        _xml_doc = SimpleXml(
            _conf_file, obj_type=EnumXmlObjType.File,
            encoding='utf-8', use_chardet=False,
            remove_blank_text=True
        )
        _status['name'] = name
        _status['url'] = _xml_doc.get_value('/down_task/info/url')
        _status['status'] = _xml_doc.get_value('/down_task/info/status')
        _status['files'] = _xml_doc.get_value('/down_task/info/files')
        _status['success'] = _xml_doc.get_value('/down_task/info/success')

        return _status

    @classmethod
    def get_down_index_info(cls, name: str, path: str) -> dict:
        """
        获取下载索引信息

        @param {str} name - 下载漫画名
        @param {str} path - 保存路径

        @returns {dict} - 信息字典, 结构与文件保存结构一致
            info : 基础信息
            down_list : 下载列表
        """
        _conf_file = os.path.join(path, name, 'down.xml')
        _xml_doc = SimpleXml(
            _conf_file, obj_type=EnumXmlObjType.File,
            encoding='utf-8', use_chardet=False,
            remove_blank_text=True
        )
        _info = {
            'info': _xml_doc.to_dict('/down_task/info')['info'],
            'down_list': _xml_doc.to_dict('/down_task/down_list')['down_list'],
        }
        return _info

    #############################
    # 任务操作函数
    #############################

    def start_job(self, job_type: str, para_dict: dict, sub_process: bool = False, asyn: bool = False, **kwargs):
        """
        启动下载任务

        @param {str} job_type - 下载任务类型，down-下载，index-获取索引文件
        @param {dict} para_dict - 任务启动参数
        @param {bool} sub_process=False - 是否用子进程模式执行（文件模式批量任务该参数无效）
        @param {bool} asyn=False - 子进程模式下，是否异步执行（不等待结果直接返回）

        @param {dict} - 非子进程模式返回处理结果字典，子进程模式返回None
        """
        _job_file = para_dict.pop('job_file', None)
        if _job_file is None and not sub_process:
            # 直接本地同步执行
            return self._run_job_local(job_type, para_dict)

        # 生成job_id，处理队列
        _job_id = str(uuid.uuid1())
        self.job_worker_num[_job_id] = int(para_dict.get('job_worker', 1))
        _queue = MemoryQueue()

        # 处理参数
        _para_dict = copy.deepcopy(para_dict)
        _para_dict['sub_process'] = 'n'  # 子任务要使用同步模式
        if _job_file is None:
            if _para_dict.get('name', '') == '':
                # 没有提供漫画名，先尝试获取，失败仍继续，只是无法获取到对应的执行进度
                try:
                    _para_dict['name'] = self.get_comics_name(_para_dict)
                except:
                    pass

            _queue.put([job_type, _para_dict])
        else:
            # 从文件中获取url列表执行下载, 通过并行方式下载
            _bytes = None
            with open(_job_file, 'rb') as _file:
                _bytes = _file.read()

            # 判断字符集
            _file_encoding = 'utf-8'
            try:
                _file_encoding = chardet.detect(_bytes)['encoding']
                if _file_encoding.startswith('ISO-8859'):
                    _file_encoding = 'gbk'
            except:
                pass

            # 处理任务添加
            _job_list = str(_bytes, encoding=_file_encoding).replace('\r', '\n').split('\n')
            for _job in _job_list:
                _job = _job.strip()
                if _job == '':
                    continue
                _job_para = copy.deepcopy(_para_dict)
                _job_infos = _job[0].split('|')
                _job_para['url'] = _job_infos[0]
                if len(_job_infos) > 1:
                    _job_para['name'] = _job_infos[1]
                else:
                    # 没有提供漫画名，先尝试获取，失败仍继续，只是无法获取到对应的执行进度
                    try:
                        _job_para['name'] = self.get_comics_name(_job_para)
                    except:
                        pass

                _queue.put([job_type, _job_para])

        # 添加到运行参数
        self.job_queues[_job_id] = _queue

        # 同步等待任务完成
        if not asyn:
            while _job_id in self.job_worker_num.keys():
                time.sleep(0.1)

    def get_running_jobs(self) -> list:
        """
        获取正在运行的下载任务清单

        @returns {list} - 任务清单数组
            [
                [name, job_id, task_id, path],
                ...
            ]
        """
        _jobs = list()
        for _job_id, _task in self.running_jobs.items():
            for _task_id, _info in _task.items():
                _jobs.append([_info['name'], _job_id, _task_id, _info['path']])

        return _jobs

    def get_task_status(self, job_id: str, task_id: str) -> dict:
        """
        获取任务执行状态

        @param {str} job_id - 工作id
        @param {str} task_id - 任务id

        @returns {dict} - 返回的状态信息
            {
                'name': '',  # 任务名
                'status': 'unknow',  # 状态包括 downloading-正在下载,done-完成下载, error-出现异常
                'files': 0,  # 总文件数
                'success': 0  # 下载成功数
            }
        """
        _status = {
            'name': '', 'status': 'unknow', 'files': 0, 'success': 0
        }
        _info = self.running_jobs.get(job_id, {}).get(task_id, None)
        if _info is not None:
            _conf_file = os.path.join(_info['path'], _info['name'], 'down.xml')
            _xml_doc = SimpleXml(
                _conf_file, obj_type=EnumXmlObjType.File,
                encoding='utf-8', use_chardet=False,
                remove_blank_text=True
            )
            _status['name'] = _info['name']
            _status['status'] = _xml_doc.get_value('/down_task/info/status')
            _status['files'] = _xml_doc.get_value('/down_task/info/files')
            _status['success'] = _xml_doc.get_value('/down_task/info/success')

        return _status

    #############################
    # 分步操作函数
    #############################

    def get_comics_name(self, para_dict: dict) -> str:
        """
        根据传入参数获取漫画名（目录名）

        @param {dict} para_dict - 下载任务请求参数，使用到的参数包括
            name : 直接送入的漫画名，如果有送入将直接使用，不会再通过url获取
            url : 可选，包含漫画卷目录索引的url地址，没有送入漫画名时必送，需要通过url获取的情况需送入
            website_driver_id : 可选，如果需要指定使用特定网站驱动时，送入对应的驱动id
            其他参数根据网站驱动的支持送入

        @returns {str} - 漫画目录名
        """
        _name = para_dict.get('name', '')
        if _name == '':
            # 需要通过url获取名字
            _url = para_dict.get('url', '')
            if _url == '':
                raise RuntimeError(_('url or name must at least set one!'))

            # 获取网站驱动
            _webdriver = DriverManager.get_website_driver(
                url=_url, class_id=para_dict.get('website_driver_id', '')
            )

            # 获取漫画名
            _name = _webdriver.get_name_by_url(**para_dict)

        _name = DownloadManager.path_char_replace(_name)
        return _name

    def get_vol_and_file_info(self, name: str, para_dict: dict) -> dict:
        """
        获取漫画卷信息和文件信息并存入下载配置

        @param {str} name - 要保存的漫画名
        @param {dict} para_dict - 下载任务请求参数，使用到的参数包括
            url : 如果是新下载必送，如果是继续下载可不送（通过name参数获取到下载配置文件的情况）
            path : 下载保存目录，不送默认为当前工作目录
            force_update : 可选，是否强制更新卷信息(y/n)，对于已完成的任务可以重新获取卷信息，默认为n
            search_mode : 可选，是否启动搜索模式(y/n), 该模式会重新遍历一次所有资源，对于已下载过的文件不再下载, 默认n
            website_driver_id : 可选，如果需要指定使用特定网站驱动时，送入对应的驱动id

        @returns {dict} - 返回的处理信息字典
            name : 漫画保存名
            path : 漫画保存路径
            url : 漫画卷目录索引url
        """
        # 获取下载文件配置
        _path = os.path.realpath(para_dict.get('path', ''))
        _url = para_dict.get('url', '')
        _xml_doc = DownloadManager.get_down_task_conf(_path, name, url=_url)

        # 获取部分配置信息
        para_dict['path'] = _path
        para_dict['name'] = name
        if _url == '':
            _url = _xml_doc.get_value('/down_task/info/url')
            para_dict['url'] = _url

        _vol_info_ok = _xml_doc.get_value('/down_task/info/vol_info_ok')
        _file_info_ok = _xml_doc.get_value('/down_task/info/file_info_ok')

        # 获取网站驱动
        _webdriver = DriverManager.get_website_driver(
            url=_url, class_id=para_dict.get('website_driver_id', '')
        )

        # 解析网页获取卷信息 - 在驱动框架已处理了自动重试
        if para_dict.get('force_update', 'n') == 'y' or para_dict.get('search_mode', 'n') == 'y' or _vol_info_ok != 'y':
            if not _webdriver.update_vol_info(_xml_doc, **para_dict):
                raise RuntimeError(_('Update vol info error'))

        # 解析网页获取每个卷的文件
        if para_dict.get('force_update', 'n') == 'y' or para_dict.get('search_mode', 'n') == 'y' or _file_info_ok != 'y':
            if not _webdriver.update_file_info(_xml_doc, **para_dict):
                raise RuntimeError(_('Update files info error'))

        # 保存信息并返回
        _xml_doc.save()

        return {'name': name, 'path': _path, 'url': _url}

    def download(self, name: str, path: str, url: str, para_dict: dict) -> dict:
        """
        对已获取卷和文件信息的下载配置进行下载处理（同步等待模式）

        @param {str} name - 漫画保存名
        @param {str} path - 漫画保存路径
        @param {str} url - 漫画卷目录索引url
        @param {dict} para_dict - 下载任务请求参数，使用到的参数包括
            auto_redo : 失败自动重试次数，默认为0


        @returns {dict} - 本次下载信息情况字典
            'name': 漫画名
            'status': 下载状态，包括done-完成下载, error-出现异常
            'msg': 失败的错误信息
            'files': 总文件数
            'success': 下载成功数
            'task': 本次处理任务数
            'task_fail': 本次处理任务失败数
        """
        # 获取配置信息
        _xml_doc = DownloadManager.get_down_task_conf(path, name, url=url)

        # 循环处理下载任务, 在有失败的情况重新执行
        _down_manager = DownloadManager(_xml_doc, **para_dict)
        _auto_redo = int(para_dict.get('auto_redo', '0'))
        _redo_time = 0
        while _redo_time <= _auto_redo:
            try:
                # 执行下载
                _down_manager.start_download()

                # 正常执行完成，检查是否已完成
                if _down_manager.down_info['task_fail'] > 0:
                    _redo_time += 1
                    time.sleep(0.01)
                    continue

                # 退出处理
                break
            except:
                _down_manager.down_info['status'] = 'error'
                _down_manager.down_info['msg'] = '%s[%s]:\n%s' % (
                    _('Download Failed'), name, traceback.format_exc()
                )
                self.print(_down_manager.down_info['msg'])
                _redo_time += 1
                time.sleep(0.01)
                continue

        # 返回处理结果
        return copy.deepcopy(_down_manager.down_info)

    #############################
    # 内部函数
    #############################
    def _run_job_local(self, job_type: str, para_dict: dict, **kwargs) -> dict:
        """
        本地运行一个任务

        @param {str} job_type - 下载任务类型，down-下载，index-获取索引文件
        @param {dict} para_dict - 下载任务请求参数，使用到的参数包括

        @returns {dict} - 本次下载信息情况字典
            'status': 下载状态，包括done-完成下载, error-出现异常
            'msg': 失败的错误信息
            'files': 总文件数
            'success': 下载成功数
            'task': 本次处理任务数
            'task_fail': 本次处理任务失败数
        """
        # 初始化下载任务请求参数
        _para_dict = Tools.get_correct_para_dict(para_dict)
        _para_dict.pop('job_file', None)  # 不支持文件这种模式的运行

        # 获取漫画名
        _name = self.get_comics_name(_para_dict)

        # 获取漫画卷和文件信息
        _info_dict = self.get_vol_and_file_info(_name, _para_dict)

        # 启动下载
        if job_type == 'index':
            # 直接返回结果
            _status = self.get_down_index_status(_name, _para_dict['path'])
            _status.update({
                'msg': 'success', 'task': '0', 'task_fail': '0'
            })
            return _status
        else:
            return self.download(
                _info_dict['name'], _info_dict['path'], _info_dict['url'], _para_dict
            )

    def _add_sub_process_task(self, job_id: str, job_type: str, para_dict: dict) -> dict:
        """
        添加子进程任务

        @param {str} job_id - 任务id
        @param {str} job_type - 下载任务类型，down-下载，index-获取索引文件
        @param {dict} para_dict - 下载参数字典

        @returns {dict} - 返回添加后的字典，失败返回None
            job_id : 返回送入的job_id
            task_id : 返回新建的任务id
            name : 传入参数的name
            popen : Popen对象
        """
        _command = {
            'down': 'download',
            'index': 'get_down_index'
        }
        try:
            # 先创建命令行
            _cmd = '%s shell_cmd="%s' % (self.execute_cmd, _command.get(job_type, 'download'))
            for _key, _val in para_dict.items():
                _cmd = '%s %s=\'%s\'' % (_cmd, _key, _val)
            _cmd += '"'

            # 创建子进程任务
            self.print('running subprocess: %s' % _cmd)
            _sp = None
            if sys.platform == 'win32':
                # windows，创建新窗口执行
                _sp = subprocess.Popen(
                    _cmd, close_fds=True, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                _sp = subprocess.Popen(_cmd, close_fds=True, shell=True)

            # 返回
            return {
                'job_id': job_id, 'task_id': str(uuid.uuid1()),
                'name': para_dict.get('name', ''), 'popen': _sp
            }
        except:
            self.print(
                'create subprocess error: %s' % traceback.format_exc()
            )
            return None

    def _monitor_thread_fun(self):
        """
        监控任务运行完成情况的线程
        """
        while not self._monitor_stop:
            try:
                # 先检查队列中是否有要发起任务的
                for _job_id, _queue in self.job_queues.items():
                    if not _queue.empty():
                        if _job_id not in self.running_jobs.keys():
                            self.running_jobs[_job_id] = dict()
                        _run_count = len(self.running_jobs[_job_id])
                        while _run_count < self.job_worker_num[_job_id]:
                            # 获取子任务
                            try:
                                _job_info = _queue.get(block=False)
                                _job_type = _job_info[0]
                                _para_dict = _job_info[1]
                            except:
                                # 取不到子任务，说明已经没有任务, 退出循环
                                break

                            # 新增执行
                            _ret = self._add_sub_process_task(_job_id, _job_type, _para_dict)
                            if _ret is None:
                                # 处理失败
                                continue

                            # 添加到运行队列中
                            self.running_jobs[_job_id][_ret['task_id']] = {
                                'name': _ret['name'], 'path': _para_dict['path'],
                                'popen': _ret['popen']
                            }
                            _run_count += 1

                # 检查每个任务的运行状态
                _job_ids = list(self.running_jobs.keys())
                for _job_id in _job_ids:
                    _task_ids = list(self.running_jobs[_job_id].keys())
                    for _task_id in _task_ids:
                        _sp: subprocess.Popen = self.running_jobs[_job_id][_task_id]['popen']
                        _poll = _sp.poll()
                        if _poll is None:
                            # 正在运行
                            continue

                        # 已到结束状态
                        if _poll == 0:
                            # 处理成功
                            self.print(
                                'job[name:%s][jid:%s][tid:%s] success!' % (
                                    self.running_jobs[_job_id][_task_id]['name'],
                                    _job_id, _task_id
                                )
                            )
                        else:
                            # 处理失败
                            self.print(
                                'job[name:%s][jid:%s][tid:%s] failure[%s]!' % (
                                    self.running_jobs[_job_id][_task_id]['name'],
                                    _job_id, _task_id, str(_poll)
                                )
                            )

                        # 删除任务记录
                        self.running_jobs[_job_id].pop(_task_id, None)

                # 清理已经完成的任务
                _job_ids = list(self.job_queues.keys())
                for _job_id in _job_ids:
                    if self.job_queues[_job_id].empty() and len(self.running_jobs[_job_id]) == 0:
                        self.job_queues.pop(_job_id)
                        self.running_jobs.pop(_job_id)
                        self.job_worker_num.pop(_job_id)

                # 休眠一会
                time.sleep(0.1)
            except:
                self.print('monitror exception: %s' % traceback.format_exc())


class BaseWebSiteDriverFW(object):
    """
    网站下载驱动框架类
    """
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
        _print = Tools.get_print_fun()
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
                    for _vol in _vol_info['vols'].keys():
                        _vol_name = DownloadManager.path_char_replace(_vol)
                        _vol_url = _vol_info['vols'][_vol]['url']

                        # 判断卷是否已经处理过
                        _vol_num_dict = json.loads(
                            xml_doc.get_value('/down_task/info/vol_num_dict', '{}')
                        )

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
                            DownloadManager.add_vol_to_down_task_conf(
                                xml_doc, _vol_name, _vol_url, status='listing'
                            )

                    # 保存下一页信息
                    _vol_next_url = _vol_info.get('vol_next_url', '')
                    xml_doc.set_value('/down_task/info/vol_next_url', _vol_next_url)
                    xml_doc.save(pretty_print=True)

                    # 检查是否有下一个url
                    if _vol_next_url != '':
                        _url = _vol_next_url
                        continue
                    else:
                        # 没有下一页, 退出循环
                        break

                # 正常执行下来，更新卷信息处理完成的标记
                xml_doc.set_value('/down_task/info/vol_info_ok', 'y')
                xml_doc.save()
                return True
            except:
                _print('%s[%s][%s]:\n%s' % (
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
        _print = Tools.get_print_fun()

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
                _vol_num_dict = json.loads(xml_doc.get_value('/down_task/info/vol_num_dict', '{}'))

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
                    if len(_file_info['files']) == 0:
                        raise RuntimeError(_('Get file info error: no file found!'))

                    # 将下载文件清单加入配置
                    _file_num = int(xml_doc.get_value(
                        '/down_task/down_list/%s/file_num' % _vol_num))
                    _file_add_num = 0
                    for _file, _down_info in _file_info['files'].items():
                        # 检查文件url是否已经存在
                        _file_exist = False
                        _real_file_name = 'file_%d' % _file_num

                        if para_dict['search_mode'] == 'y':
                            # 搜索模式，从所有文件url判断
                            if xml_doc.get_value("//url[text()='%s']" % _down_info['url']) != '':
                                # 找到文件已存在
                                _file_exist = True
                        else:
                            # 非搜索模式，仅判断当前卷
                            if xml_doc.get_value("/down_task/down_list/%s/files/%s/url[text()='%s']" % (_vol_num, _real_file_name, _down_info['url'])) != '':
                                # 找到文件已存在
                                _file_exist = True

                        if not _file_exist:
                            # 文件不存在，新增
                            _file_num += 1
                            _file_add_num += 1
                            _fix_file_name = DownloadManager.path_char_replace(_file)
                            if len(_fix_file_name) > 100:
                                # 限制文件名长度
                                _ext = FileTool.get_file_ext(_fix_file_name)
                                _fix_file_name = _fix_file_name[0: 99 - len(_ext)] + '.' + _ext

                            DownloadManager.add_file_to_down_task_conf(
                                xml_doc, _vol_num, _real_file_name,
                                _fix_file_name,
                                _down_info['url'],
                                _down_info['downtype'],
                                extend_json=_down_info.get('extend_json', None)
                            )

                    # 更新_last_tran_para
                    _last_tran_para = _file_info.get('next_tran_para', None)

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
                _print('%s[%s][%s][%s]:\n%s' % (
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
            key - 网站主域名, 比如www.youku.com
            value - dict {
                'remark': '网站说明'
                'subsite': ['子域名', '子域名', ...]
            }
        """
        raise NotImplementedError()

    @classmethod
    def get_name_by_url(cls, **para_dict) -> str:
        """
        根据url获取下载漫画名
        (需继承类实现)

        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
            关键参数包括:
            url - 漫画所在目录索引页面的url

        @returns {str} - 返回漫画名
        """
        raise NotImplementedError()

    @classmethod
    def _get_vol_info(cls, index_url: str, **para_dict) -> dict:
        """
        获取漫画的卷列表信息
        (需继承类实现)

        @param {str} index_url - 漫画所在目录索引的url
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来

        @returns {dict} - 返回 vols_info 卷信息字典
            vol_next_url {str} - 传入下一页的url，如果没有下一页可以不传或传''
                注：应用会根据vol_next_url判断要不要循环获取卷信息
            vols {dict} - 卷信息字典(dict), key为卷名，value卷信息字典
                    url {str} - 为浏览该卷漫画的url
                注：卷名可以通过标签‘{$path_split$}’来设置卷保存的子目录
        """
        raise NotImplementedError()

    @classmethod
    def _get_file_info(cls, vol_url: str, last_tran_para: object = None, **para_dict) -> dict:
        """
        获取对应卷的下载文件清单

        @param {str} vol_url - 浏览该卷漫画的url
        @param {object} last_tran_para=None - 传入上一次文件信息获取完成后传递的自定义参数对象
            注：可以利用这个参数传递上一个卷的文件信息获取所形成的公共变量，减少当前卷文件处理所需计算量
            例如假设所有卷的文件信息都来源于同一个页面，可以通过该参数传递浏览器对象，避免下一个卷处理需要再次打开浏览器
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来

        @returns {dict} - 返回 files_info 文件信息字典
            next_tran_para {object} - 要传入下一次执行的参数对象（实现类自定义）
            files {dict} - 下载文件信息字典(dict), key为文件名, value为文件信息字典
                url {str} - 文件下载url地址
                downtype {str} - 指定文件下载类型（具体支持类型需参考装载的下载驱动, 默认将支持http/ftp）
                extend_json {dict} - 要送入下载驱动的扩展信息字典
            ...
        """
        raise NotImplementedError


class BaseDownDriverFW(object):
    """
    文件下载驱动框架
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
        raise NotImplementedError()

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
        raise NotImplementedError()


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))
