#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
网站驱动手工测试
@module website_driver_test
@file website_driver_test.py
"""

import sys
import os
import json
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from comics_down.lib.core import Tools, BaseWebSiteDriverFW, DriverManager
from comics_down.website_driver.youku_website_driver import YouKuPlayListDriver
from comics_down.website_driver.common_website_driver import CommonDriver


class TestWebSiteDriver(object):
    """
    测试网站驱动的通用类
    """
    @classmethod
    def init_driver(cls):
        DriverManager.init_drivers(
            os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, 'comics_down')),
            common_wd_overwrite=True
        )

    @classmethod
    def test_get_name_by_url(cls, driver: BaseWebSiteDriverFW, para_dict: dict):
        """
        测试获取漫画名

        @param {object} driver - 驱动类对象
        @param {dict} para_dict - 执行字典
        """
        _para_dict = Tools.get_correct_para_dict(para_dict)
        print(
            'get_name:',
            driver.get_name_by_url(**_para_dict)
        )

    @classmethod
    def test_get_vol_info(cls, driver: BaseWebSiteDriverFW, url: str, para_dict: dict):
        """
        测试获取卷信息

        @param {object} driver - 驱动类对象
        @param {str} url - 获取卷的地址
        @param {dict} para_dict - 执行字典
        """
        _para_dict = Tools.get_correct_para_dict(para_dict)
        _info = driver._get_vol_info(url, **_para_dict)
        print(
            'get_vols:',
            json.dumps(_info, ensure_ascii=False, indent=2)
        )

    @classmethod
    def test_get_file_info(cls, driver: BaseWebSiteDriverFW, url: str, para_dict: dict):
        """
        获取卷的文件下载信息

        @param {object} driver - 驱动类对象
        @param {str} url - 卷的地址
        @param {dict} para_dict - 执行字典
        """
        _para_dict = Tools.get_correct_para_dict(para_dict)
        _info = driver._get_file_info(url, None, **_para_dict)
        print(
            'get_files:',
            json.dumps(_info, ensure_ascii=False, indent=2)
        )


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    TestWebSiteDriver.init_driver()

    # 控制测试环节的字典
    _control = {
        'name': True,  # 测试名字获取
        'vol_info': True,  # 测试获取卷信息
        'file_info': True  # 测试获取文件信息
    }

    _test_vol_url = {
        'v.youku.com': [
            'https://v.youku.com/v_show/id_XMzU2MTExMzI4OA==.html?spm=a2hcb.12701310.app.5~5!2~5!3~5~5~5!8~5~5~5~A&s=d4a1c61a5c114a6e89e9',
            'https://v.youku.com/v_show/id_XNTQwMTgxMTE2.html?spm=a2ha1.14919748_WEBCOMIC_JINGXUAN.drawer4.d_zj1_1&s=cc001f06962411de83b1&scm=20140719.apircmd.4392.show_cc001f06962411de83b1',
            'https://v.youku.com/v_show/id_XNTEyNzkwMDk0NA==.html?spm=a2hcb.12701310.app.5~5!2~5!3~5~5~5!32~5~5~5~A&s=cefa4220b0ea4a3f8795'
        ],
        "www.edddh.net": [
            'http://www.edddh.net/vod/zuiewangguan/'
        ],
        "www.77mh.de": [
            'https://www.77mh.de/colist_246264.html'
        ],
        "www.mangabz.com": [
            'http://www.mangabz.com/266bz/'
        ]
    }

    _test_file_url = {
        'www.77mh.de': [
            'https://www.77mh.de//202012/473190.html'
        ],
        'www.mangabz.com': [
            'http://www.mangabz.com//m180970/'
        ]
    }

    # 要测试的地址
    _site = 'www.mangabz.com'
    _pos = 0

    # 基础参数设置
    _driver_class = CommonDriver

    _get_name_url = _test_vol_url[_site][_pos]
    _get_vol_url = _get_name_url
    _get_file_url = _test_file_url.get(_site, None)
    if _get_file_url is None:
        _get_file_url = _get_vol_url
    elif len(_get_file_url) > _pos:
        _get_file_url = _get_file_url[_pos]
    else:
        _get_file_url = _get_file_url[0]

    # 设置要送入的参数默认值
    _para_dict = {
        'url': _get_name_url,
        'debug_path': '/Users/lhj/downtest'
    }

    if _control['name']:
        TestWebSiteDriver.test_get_name_by_url(
            _driver_class, _para_dict
        )

    if _control['vol_info']:
        TestWebSiteDriver.test_get_vol_info(
            _driver_class, _get_vol_url, _para_dict
        )

    if _control['file_info']:
        TestWebSiteDriver.test_get_file_info(
            _driver_class, _get_file_url, _para_dict
        )
