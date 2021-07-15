#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
网页自动分析功能测试
@module auto_analyse_test
@file auto_analyse_test.py
"""

import sys
import os
import json
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from comics_down.lib.core import Tools
from comics_down.lib.auto_analyse import AnalyzeTool


class TestAutoAnalyse(object):
    """
    自动分析测试类
    """
    pass


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    _para_dict = Tools.get_correct_para_dict({})

    _config = AnalyzeTool.get_contents_config(
        [
            'http://www.edddh.net/vod/quanzhilierenjuchangbanzuihouderenwu/',
            'http://www.edddh.net/vod/guaihuamao1/'
        ],
        {
            # 'name': ['全职猎人剧场版：最后的任务', '怪化猫'],
            # 'time': ['2021-06-20 15:57:29', '2021-06-17 23:25:32'],
            'nick': ['全职猎人2013剧场版: 最后的使命/全职猎人The Last Mission', 'モノノ怪/物怪/Mononoke']
        },
        is_tail=True,
        use_html_code=True,
        search_dict={
            'selector_up_level': '3'
        },
        **_para_dict
    )
    print(_config)
