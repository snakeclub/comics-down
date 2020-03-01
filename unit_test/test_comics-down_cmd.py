#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import os
import unittest
from HiveNetLib.simple_i18n import _, SimpleI18N, set_global_i18n
from HiveNetLib.base_tools.run_tool import RunTool
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from mediawikiTool.lib.mediawiki_cmd import MediaWikiCmd


_TEST_DATA_DIR = os.path.abspath(os.path.dirname(__file__) + '/' +
                                 '../test_data/').replace('\\', '/')
_TEMP_DIR = os.path.abspath(os.path.dirname(__file__) + '/' +
                            '../test_data/temp/').replace('\\', '/')
_I18N_File_DIR = os.path.abspath(os.path.dirname(__file__) + '/' +
                                 '../mediawikiTool/i18n/').replace('\\', '/')


def setUpModule():
    # print("test module start >>>>>>>>>>>>>>")
    _i18n_obj = SimpleI18N(
        lang='zh_cn',
        trans_file_path=_I18N_File_DIR,
        trans_file_prefix='message',
        auto_loads=True
    )
    set_global_i18n(_i18n_obj)
    RunTool.set_global_var('CONSOLE_GLOBAL_PARA', dict())


def tearDownModule():
    # print("test module end >>>>>>>>>>>>>>")
    pass


class Test(unittest.TestCase):

    # 整个Test类的开始和结束执行
    @classmethod
    def setUpClass(cls):
        # print("test class start =======>")
        pass

    @classmethod
    def tearDownClass(cls):
        # print("test class end =======>")
        pass

    # 每个用例的开始和结束执行
    def setUp(self):
        # print("test case start -->")
        pass

    def tearDown(self):
        # print("test case end -->")
        pass

    def test_mdtowiki(self):
        # mdtowiki -in D:\opensource\mediawikiTool\test_data\mediawiki_cmd\mdtowiki.md -out D:\opensource\mediawikiTool\test_data\temp\mediawiki_cmd -stdpic
        # mdtowiki -in D:\opensource\mediawikiTool\test_data\mediawiki_cmd\mdtowiki.md -out D:\opensource\mediawikiTool\test_data\temp\mediawiki_cmd -name my_testmdtowiki -stdpic
        print("test mdtowiki")
        _mediawiki_cmd = MediaWikiCmd()
        _result = _mediawiki_cmd.cmd_dealfun(
            message='', cmd='mdtowiki',
            cmd_para='-in %s/mediawiki_cmd/mdtowiki.md -out %s/mediawiki_cmd/ -stdpic' % (
                _TEST_DATA_DIR, _TEMP_DIR
            )
        )
        for _ret_str in _result:
            print(_ret_str)

    def test_docxtowiki(self):
        # docxtowiki -in D:\opensource\mediawikiTool\test_data\mediawiki_cmd\docxtowik.docx -out D:\opensource\mediawikiTool\test_data\temp\mediawiki_cmd
        print("test docxtowiki")
        _mediawiki_cmd = MediaWikiCmd()
        _result = _mediawiki_cmd.cmd_dealfun(
            message='', cmd='docxtowiki',
            cmd_para='-in %s/mediawiki_cmd/docxtowik.docx -out %s/mediawiki_cmd/' % (
                _TEST_DATA_DIR, _TEMP_DIR
            )
        )
        for _ret_str in _result:
            print(_ret_str)


if __name__ == '__main__':
    unittest.main()
