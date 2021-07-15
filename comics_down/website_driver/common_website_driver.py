#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
通用的网站下载驱动（通过配置文件处理）
@module common_website_driver
@file common_website_driver.py
"""

import os
import sys
import copy
from urllib.parse import urlparse
from HiveNetLib.base_tools.net_tool import NetTool
from HiveNetLib.html_parser import HtmlParser
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import BaseWebSiteDriverFW, Tools
from comics_down.lib.webdriver_tool import WebDriverTool
from comics_down.lib.auto_analyse import AnalyzeTool


class CommonDriver(BaseWebSiteDriverFW):
    """
    通用的下载驱动
    """
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
        # 从配置中获取支持网站清单并返回
        _configs = Tools.get_common_website_configs()
        _dict = dict()
        for _key, _congfig in _configs.items():
            if _key == 'mapping':
                continue

            for _host, _infos in _congfig.items():
                _dict[_host.lower()] = {
                    'remark': _infos.get('remark', ''),
                    'subsite': copy.deepcopy(_infos.get('subsite', []))
                }

        return _dict

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
        # 获取配置
        _config = cls._get_config(para_dict['url'], 'name')

        # 更新任务执行参数
        _para_dict = para_dict
        if _config.get('para_dict', '') != '':
            _para_dict.update(_config['para_dict'])

        # 获取网页处理对象
        if _config.get('is_html_code', True):
            # 静态页面获取
            _html_code = WebDriverTool.get_web_page_code(
                _para_dict, headers=_config.get('headers', None)
            )
            _web_obj = HtmlParser(_html_code)
        else:
            # 获取dom对象
            _web_obj = WebDriverTool(
                _para_dict, roll_to_end=_config.get('roll_to_end', False),
                until=_config.get('until', '')
            )

        _ret = cls.run_scripts(
            _config.get('scripts', []), _web_obj, sub_scripts=_config.get('sub_scripts', {})
        )

        # 返回漫画名, 要求传出的参数必须有name这个变量
        return _ret['vars']['name'].strip()

    @classmethod
    def _get_vol_info(cls, index_url: str, **para_dict):
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
        # 获取配置
        _config = cls._get_config(index_url, 'vol')
        if _config is None:
            return {
                'vol_next_url': '',
                'vols': {
                    'Video': {'url': index_url}
                }
            }

        # 更新任务执行参数
        _para_dict = para_dict
        _para_dict['url'] = index_url
        if _config.get('para_dict', '') != '':
            _para_dict.update(_config['para_dict'])

        # 获取网页处理对象
        _web_obj = None
        if _web_obj is None:
            if _config.get('is_html_code', True):
                # 静态页面获取
                _html_code = WebDriverTool.get_web_page_code(
                    _para_dict, headers=_config.get('headers', None)
                )
                _web_obj = HtmlParser(_html_code)
            else:
                # 获取dom对象
                _web_obj = WebDriverTool(
                    _para_dict, roll_to_end=_config.get('roll_to_end', False),
                    until=_config.get('until', '')
                )

        # 运行完成后，要求传出参数包含 vol_next_url 变量, 该变量字符串，如果无需处理可返回''
        # 要求传出参数包含 vols 变量，每个项为一个卷信息数组，顺序为卷名、url
        _ret = cls.run_scripts(
            _config.get('scripts', []), _web_obj, sub_scripts=_config.get('sub_scripts', {})
        )
        _vols = _ret['vars']['vols']

        # url均需进行处理
        _vol_next_url = _ret['vars'].get('vol_next_url', '')
        if _vol_next_url != '':
            _vol_next_url = NetTool.get_full_url(_vol_next_url, index_url)

        _vols_info = {
            'vol_next_url': _vol_next_url,
            'vols': dict()
        }

        for _info in _vols:
            _vols_info['vols'][_info[0].strip()] = NetTool.get_full_url(_info[1], index_url)

        return _vols_info

    @classmethod
    def _get_file_info(cls, vol_url: str, last_tran_para: object, **para_dict):
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
        # 获取配置
        _config = cls._get_config(vol_url, 'file')

        # 更新任务执行参数
        _para_dict = para_dict
        _para_dict['url'] = vol_url
        if _config.get('para_dict', '') != '':
            _para_dict.update(_config['para_dict'])

        _web_obj = None
        if last_tran_para is not None and type(last_tran_para) == dict:
            # 从上一次执行传入的要处理的对象
            if last_tran_para.get('web_obj', None) is not None:
                _web_obj = last_tran_para['web_obj']

        # 获取网页处理对象
        if _web_obj is None:
            if _config.get('is_html_code', True):
                # 静态页面获取
                _html_code = WebDriverTool.get_web_page_code(
                    _para_dict, headers=_config.get('headers', None)
                )
                _web_obj = HtmlParser(_html_code)
            else:
                # 获取dom对象
                _web_obj = WebDriverTool(
                    _para_dict, roll_to_end=_config.get('roll_to_end', False),
                    until=_config.get('until', '')
                )

        # 运行完成后，要求传出参数包含 next_tran_para 变量, 该变量为字典，如果无需处理则传入None
        # 要求传出参数包含 files 变量，每个项为一个文件信息数组，顺序为文件名、url、downtype、extend_json
        # 要求传出参数包括 files_deal 变量，为一个指令字典，指定对文件信息的后处理要求，目前支持:
        #   media_by_page - 指定url为页面地址，需通过页面获取实际url下载地址，value为媒体文件类型清单
        _ret = cls.run_scripts(
            _config.get('scripts', []), _web_obj, sub_scripts=_config.get('sub_scripts', {})
        )
        _files = _ret['vars']['files']
        _files_deal = _ret['vars'].get('files_deal', {})
        _media_by_page = _files_deal.get('media_by_page', '')

        _files_info = {
            'next_tran_para': _ret['vars'].get('next_tran_para', None),
            'files': {}
        }

        # 遍历处理文件
        _media_para_dict = copy.deepcopy(_para_dict)
        _media_para_dict.pop('url', None)
        for _info in _files:
            _url = NetTool.get_full_url(_info[1], vol_url)
            if _media_by_page != '':
                _url = AnalyzeTool.get_media_url(_url, type_list=_media_by_page, **_media_para_dict)
                if _url == '':
                    raise FileNotFoundError('media not found in [%s]' % _info[1])

            _files_info['files'][_info[0].strip()] = {
                'url': NetTool.get_full_url(_url, vol_url),
                'downtype': _info[2],
                'extend_json': _info[3]
            }

        return _files_info

    #############################
    # 公共函数
    #############################

    @classmethod
    def run_scripts(cls, scripts: list, web_object: WebDriverTool, sub_scripts: dict = {}, para_dict: dict = {},
                    els: list = None, vars: dict = {}) -> dict:
        """
        执行脚本并返回最后一步的结果

        @param {list} scripts - 传入要执行的脚本清单
            查找类动作：
            ['pos': 0],  # 获取当前清单中指定位置的元素
            ['children'],  # 获取当前清单元素中的所有子元素
            ['id', 'myId'],  # 通过id获取元素
            ['xpath', '//img[@id="dracga" and @style]'],  # 通过xpath获取元素
            ['name', 'myName'],  # 通过元素的name属性获取
            ['tag_name', 'img'],  # 通过元素的标签名获取
            ['class_name', 'styleClass'],  # 通过元素的class名获取
            ['css_selector', '#kw'],  # 通过css选择器方式获取，id用#kw, class用.s_ipt, 与css的简写方式相同
            ['link_text', 'hao123'],  # 通过超文本链接上的文字信息来定位元素
            ['partial_link_text', 'hao']  # 通过超文本连接上的文字的一部分关键字信息来定位元素

            浏览器操作类动作：
            ['wait', '0.1'],  # 等待指定的秒数
            ['open_window', 'chrome://downloads/'],  # 打开新标签页，参数为要打开的页面url
            ['close_window', 'int/str'],  # 关闭指定页签，如果不传值代表关闭当前页签
                # 如果第一个参数为int类型，代表关闭指定位置的页签
                # 如果第一个参数为str类型，代表关闭title为送入参数的页签
            ['switch_to', 'frame/parent_frame/default/alert/window', ...],  # 切换浏览器页面
                # frame-切换到当前元素清单第1个的frame中，parent_frame-切换到父页面，default-切换到最外层页面
                # alert-切换到浏览器弹出框，后续可以带对弹出框的操作: 'accept'-点击确认按钮，'dismiss'-点击取消按钮
                # window-切换到指定页签，后续第一个参数如果为数字，代表切换到指定位置的窗口(开始为0，可以用-1指示最后一个)
                #   后续第一个参数如果为文本，代表通过窗口标题来获取对应的窗口
            ['scroll_into_view'],  # 将当前元素滚动到可视范围
            ['run_script', 'window.alert(\'这是一个测试Alert弹窗\');']  # 执行js脚本
            ['click'] # 点击元素
            ['send_str', '要输入的文本'] # 元素输入文本
            ['send_keys', 'Keys.CONTROL', 'Keys.SHIFT', 'a', ...]  # 输入按键，传入多个代表同时按下
                # 特殊按键定义参考 selenium.webdriver.common.keys.Keys

            脚本类操作：
            ['set_to_var', '变量访问名', '取值类型', 'para', ...]  # 将相应的值存入指定变量, 取值类型和参数说明如下:
                'elements' - 无参数，将当前的元素清单放入变量
                'eval' - 放入python脚本执行的结果，参数为python脚本，处理中将通过eval方法计算和得出，因此需注意使用python语法
                'el_infos' - 将当前元素清单的信息按数组方式顺序放入变量，每个参数为一个取值公式，定义如下：
                    '@xxx' - 获取属性名为xxx的值，'.脚本'- 尝试用'el.脚本'方式执行获取(例如'.tag_name'获取标签名, '.text' - 获取文本)
                    'python脚本' - 尝试用eval计算得出值
                'el_info' - 将当前元素清单的第1个元素的特定取值放入变量，参数为取值公式，定义与el_infos定义一致
                'sub_el_infos' - 将当前元素清单的子对象的信息按数组方式顺序放入变量，每个参数为一个取值公式
                    第一个参数为获取子对象的xpath，后面的取值参数与el_infos定义一致
                'sub_el_info' - 将当前元素清单第1个元素的子对象的特定取值放入变量,
                    第一个参数为获取子对象的xpath，后面的取值参数与el_infos定义一致
            ['els_from_var', '变量访问名'] - 从变量中获取元素清单更新到当前元素清单中
            ['remove_var', '变量访问名'] - 删除变量
            ['if', '条件脚本', 'true时执行的子脚本标识', 'false时执行的子脚本标识'] - if处理
            ['while', '条件脚本', '满足条件循环执行的子脚本'] - while处理
            ['each', '对清单中每个对象要执行的子脚本', '取值类型', 'para', ...] - 对list的每个对象逐个执行处理，取值类型和参数说明如下：
                'elements' - 无参数，遍历当前的元素清单
                'eval' - 放入python脚本执行的结果，参数为python脚本
                'var' - 从变量获取，参数为变量名
                注：取到的每个对象会存入变量名为 '{$current_each_item$}' 的对象中，同时 {$current_each_index$} 变量名存储当前循环位置
            ['exec', 'python脚本'] - 要执行的python脚本

        @param {HtmlParser|WebDriverTool} web_object - 要操作的对象
        @param {dict} sub_scripts={} - 子脚本清单，key为脚本标识，value为该子脚本的执行数组
        @param {dict} para_dict={} - 送入任务执行参数，内部可以直接访问该参数
        @param {list} els=None - 当前的元素清单，如果为执行子脚本情况，送入当前找到的元素清单, 内部脚本可直接使用
        @param {dict} vars={} - 如果为子脚本情况，送入当前变量字典，子脚本可以访问和修改相应的变量，内部脚本可直接使用

        @returns {dict} - 结果字典
            {
                'els' : 当前查询到的对象列表
                'vars' : 执行过程通过脚本类操作保留下来的变量值，key为变量名, value为变量值
            }
        """
        #############################
        # 内部定义函数
        #############################
        def _get_el_infos(_els: list, _paras: list) -> list:
            """
            根据元素清单获取对应的取值数组

            @param {list} _els - 元素清单
            @param {list} _paras - 取值公式数组，每个参数定义如下：
                '@xxx' - 获取属性名为xxx的值，'.脚本'- 尝试用'el.脚本'方式执行获取(例如'.tag_name'获取标签名, '.text' - 获取文本)
                'python脚本' - 尝试用eval计算得出值

            @returns {list} - 返回的取值结果数组，每个项为元素对应的取值结果数组
            """
            _infos = list()
            for _el in _els:
                _el_info = list()
                for _para in _paras:
                    if _para.startswith('@'):
                        # 取属性值
                        _el_info.append(_el.get_attribute(_para[1:]))
                    elif _para.startswith('.'):
                        # 视为执行函数
                        _el_info.append(eval('_el%s' % _para))
                    else:
                        # 视为执行eval
                        _el_info.append(eval(_para))
                _infos.append(_el_info)

            return _infos

        #############################
        # 开始正式的处理
        #############################
        if vars is None:
            vars = dict()  # 变量字典

        for _step in scripts:
            _action = _step[0]
            if _action in ('pos', 'children', 'id', 'xpath', 'name', 'tag_name', 'class_name', 'css_selector', 'link_text', 'partial_link_text'):
                # 查询类处理
                if els is None:
                    els = web_object.find_elements([_step])  # 视为无父节点的情况执行
                else:
                    _find_els = list()
                    for _el in els:
                        _find_els.extend(web_object.find_elements([_step], parent=_el))
                    els = _find_els
            elif _action in ('wait', 'open_window', 'close_window', 'switch_to', 'scroll_into_view', 'run_script', 'click', 'send_str', 'send_keys'):
                # 操作类处理
                if els is None:
                    # 初始情况不执行
                    continue
                for _el in els:
                    web_object.do_script([_step], parent=_el)
            else:
                # 脚本类操作
                if _action == 'set_to_var':
                    # 向变量中存值
                    if _step[2] == 'elements':
                        vars[_step[1]] = els
                    elif _step[2] == 'eval':
                        vars[_step[1]] = eval(_step[3])
                    elif _step[2] in ('el_infos', 'el_info', 'sub_el_infos'):
                        if els is None:
                            vars[_step[1]] = None
                            continue

                        if _step[2] == 'el_infos':
                            # 将当前元素清单的信息按数组方式顺序放入变量
                            _infos = _get_el_infos(els, _step[3:])
                            vars[_step[1]] = _infos
                        elif _step[2] == 'el_info':
                            # 将当前元素清单的第1个元素的特定取值放入变量
                            _infos = _get_el_infos([els[0], ], _step[3:])
                            vars[_step[1]] = _infos[0][0]
                        elif _step[2] == 'sub_el_infos':
                            # 将当前元素清单的子对象的信息按数组方式顺序放入变量
                            _infos = list()
                            for _el in els:
                                _sub_els = web_object.find_elements(
                                    [['xpath', _step[3]]], parent=_el
                                )
                                if _sub_els is not None and len(_sub_els) > 0:
                                    _infos.extend(
                                        _get_el_infos(_sub_els, _step[4:])
                                    )
                            # 元素信息存入变量
                            vars[_step[1]] = _infos
                        else:
                            _sub_els = web_object.find_elements(
                                [['xpath', _step[3]]], parent=els[0]
                            )
                            if _sub_els is not None and len(_sub_els) > 0:
                                _infos = _get_el_infos([_sub_els[0], ], _step[4:])
                                vars[_step[1]] = _infos[0][0]
                            else:
                                vars[_step[1]] = None
                elif _action == 'els_from_var':
                    # 从变量中取值设置当前元素清单
                    els = vars[_step[1]]
                elif _action == 'remove_var':
                    vars.pop(_step[1], None)
                elif _action == 'if':
                    _condition = eval(_step[1])
                    if _condition:
                        # 执行true子脚本
                        cls.run_scripts(
                            sub_scripts[_step[2]], web_object, sub_scripts=sub_scripts,
                            els=els, vars=vars
                        )
                    elif len(_step) > 3:
                        # 执行fasle子脚本
                        cls.run_scripts(
                            sub_scripts[_step[3]], web_object, sub_scripts=sub_scripts,
                            els=els, vars=vars
                        )
                elif _action == 'while':
                    while eval(_step[1]):
                        # 循环执行子脚本
                        cls.run_scripts(
                            sub_scripts[_step[2]], web_object, sub_scripts=sub_scripts,
                            els=els, vars=vars
                        )
                elif _action == 'each':
                    # 遍历执行
                    if _step[2] == 'elements':
                        _item_list = els
                    elif _step[2] == 'eval':
                        _item_list = eval(_step[3])
                    elif _step[2] == 'var':
                        _item_list = vars[_step[3]]
                    else:
                        raise KeyError('action para error: %s' % str(_step))

                    vars['{$current_each_index$}'] = 0
                    for _item in _item_list:
                        vars['{$current_each_item$}'] = _item
                        cls.run_scripts(
                            sub_scripts[_step[1]], web_object, sub_scripts=sub_scripts,
                            els=els, vars=vars
                        )
                        vars['{$current_each_index$}'] += 1
                elif _action == 'exec':
                    # 执行脚本
                    exec(_step[1])

        # 返回处理结果
        return {
            'els': els,
            'vars': vars
        }

    #############################
    # 内部函数
    #############################

    @classmethod
    def _get_config(cls, url: str, config_type: str) -> dict:
        """
        根据url和类型获取配置信息

        @param {str} url - 要匹配的url
        @param {str} config_type - 配置类型，name/vol/file

        @returns {dict} - 返回配置字典
        """
        _host = urlparse(url).netloc
        _configs = Tools.get_common_website_configs()
        _uuid = _configs['mapping'].get(_host.upper(), None)
        if _uuid is None:
            raise FileNotFoundError('website config for [%s] is not found' % _host)

        _type_config = list(_configs[_uuid[0]].values())[0].get(
            'configs', {}
        ).get(config_type, None)

        # 修正字典异常值
        if _type_config is not None:
            _headers = _type_config.get('headers', None)
            if _headers == '':
                _type_config['headers'] = None

            _sub_scripts = _type_config.get('sub_scripts', None)
            if _sub_scripts == '':
                _type_config['sub_scripts'] = {}

        return _type_config
