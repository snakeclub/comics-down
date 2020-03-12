#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
下载工具模块
@module down_tool
@file down_tool.py
"""
import os
import sys
import time
import threading
import traceback
import HiveNetLib.base_tools.wget as wget
from HiveNetLib.base_tools.run_tool import RunTool
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.base_tools.net_tool import NetTool
from HiveNetLib.simple_i18n import _
from HiveNetLib.simple_xml import SimpleXml, EnumXmlObjType
from HiveNetLib.simple_queue import MemoryQueue
from HiveNetLib.simple_parallel import ParallelPool, ThreadParallel, ThreadParallelLock, ThreadParallelShareDict
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))


__MOUDLE__ = 'down_tool'  # 模块名
__DESCRIPT__ = u'下载工具模块'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.02.29'  # 发布日期


#############################
# 下载配置文件格式
# down_task
#     info : 基本信息
#         name : 漫画名(任务名, 也是path下的漫画目录名)
#         url : 漫画所在目录索引页面的url
#         status : 下载状态, downloading, done
#         vol_info_ok : 卷清单是否已更新成功
#         file_info_ok : 文件清单是否已更新成功
#         files : 总文件数
#         success : 成功下载数
#         vol_num : 最大卷号
#         vol_num_dict : 卷名和卷id的对应关系字典字符串
#         vol_next_url : 处理卷目录时如果存在多页的情况，在一页成功后传入下一页的url
#     down_list : 下载清单
#         vol_[num] : 卷id
#             name : 卷名(也是卷目录名)
#             url : 目录对应的浏览url
#             status : 下载状态, listing, downloading, done
#             file_num : 最大文件号
#             files : 要下载的文件清单
#                 file_[num] : 文件标识
#                     name : 文件名
#                     url : 下载的url
#                     status : 下载状态, err, done
#                     downtype : 下载类型，目前支持：http, ftp
#     error : 本次处理的异常信息（每次启动会删除）
#         vol_[num]
#             name : 卷名(也是卷目录名)
#             url : 目录对应的浏览url
#             files : 要下载的文件
#                 file_[num] : 文件标识
#                     name : 文件名
#                     url : 下载的url
#############################


class DownTool(object):
    """
    下载工具类
    """
    #############################
    # 静态方法
    #############################
    @staticmethod
    def path_char_replace(path: str, replace_str='_'):
        """
        将目录中的特殊字符进行替换
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
            _xml_doc.set_value('/down_task/info/vol_num_dict', '')
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
        @param {str} status='err' - 状态

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
        _vol_num_dict = xml_doc.get_value('/down_task/info/vol_num_dict', default='')
        if _vol_num_dict == '':
            _vol_num_dict = dict()
        else:
            _vol_num_dict = eval(_vol_num_dict)

        _vol_num_dict[vol_name] = _vol_num
        xml_doc.set_value('/down_task/info/vol_num_dict', str(_vol_num_dict))

        # 保存
        xml_doc.save(pretty_print=True)

        # 返回处理结果
        return _vol_num

    @staticmethod
    def add_file_to_down_task_conf(xml_doc: SimpleXml, vol_num: str, file_num: str,
                                   file_name: str, url: str, downtype: str):
        """
        将文件信息加入到任务配置文件（注意该方法不保存配置）

        @param {SimpleXml} xml_doc - 配置文件对象
        @param {str} vol_num - 卷标识
        @param {str} file_num - 文件标识
        @param {str} file_name - 文件名
        @param {str} url - 下载url
        @param {str} downtype - 下载类型
        """
        _xpath = '/down_task/down_list/%s/files/%s' % (vol_num, file_num)
        xml_doc.set_value('%s/name' % _xpath, file_name)
        xml_doc.set_value('%s/url' % _xpath, url)
        xml_doc.set_value('%s/status' % _xpath, '')
        xml_doc.set_value('%s/downtype' % _xpath, downtype)

    #############################
    # 需要初始化处理的方法
    #############################
    def __init__(self, xml_doc, **para_dict):
        """
        构造函数

        @param {SimpleXml} xml_doc - 下载配置文件的操作对象
        @param {dict} para_dict - 扩展参数, 任务的执行参数都会传进来
        """
        self.xml_doc = xml_doc
        self.para_dict = para_dict
        self.lock = threading.RLock()
        self.listing_vol = 0  # 没有正确获取到文件清单的卷数

        self.down_vol_info = dict()  # 用于登记每个卷下载图片数的字典
        self.down_queue = MemoryQueue()  # 下载下载任务的队列
        self.down_info = RunTool.get_global_var('JOB_RESULT')[self.para_dict['name']]
        self.down_driver_dict = RunTool.get_global_var('DOWN_DRIVER_DICT')

    def start_down_file(self):
        """
        启动下载文件处理
        """
        # 启动任务时重新获取所有文件数量
        self.down_info['files'] = int(self.xml_doc.get_value('/down_task/info/files'))
        self.down_info['success'] = int(self.xml_doc.get_value('/down_task/info/success'))

        # 将下载任务放入队列
        self._add_down_task_to_queue()

        # 检查下载队列情况
        if not self._check_down_status():
            # 没有待下载数据
            return

        # 创建进程池
        _pool = ParallelPool(
            deal_fun=self._down_worker_fun,
            parallel_class=ThreadParallel,
            run_args=(self.down_queue, ),
            task_queue=self.down_queue,
            maxsize=int(self.para_dict['job_down_worker']),
            worker_overtime=float(self.para_dict['down_overtime']),
            replace_overtime_worker=True,
            sharedict_class=ThreadParallelShareDict,
            parallel_lock_class=ThreadParallelLock,
            auto_stop=True
        )
        # 启动线程池
        _pool.start()

        # 等待任务结束
        while not _pool.is_stop:
            time.sleep(1)

        # 再次检查任务
        self._check_down_status()

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
            regex_str='^.*\.(TMP|tmp)$',
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

                # 卷id，文件id，卷名，文件名，文件下载url， 下载类型
                _file_name = _file_list[_file]['name']
                self.down_queue.put(
                    [
                        _vol_num, _file, _vol_name, _file_name,
                        _file_list[_file]['url'], _file_list[_file]['downtype']]
                )

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
            if os.path.exists(_save_file):
                FileTool.remove_file(_save_file)

            if not os.path.exists(_save_path):
                FileTool.create_dir(_save_path, exist_ok=True)

            # 执行下载
            if _task[5] not in self.down_driver_dict.keys():
                # 不支持的下载类型
                raise RuntimeError(_('not support downtype [$1]', _task[5]))

            _down_class = self.down_driver_dict[_task[5]]
            _down_class.download(_url, _save_file, **self.para_dict)

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

            print('%s[%s -> %s]: %s' % (_('DownLoad Sucess'), _task[0], _task[1], _url))
            time.sleep(1)
            return True
        except:
            # 下载失败
            print(traceback.format_exc())
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
                print('%s:\n%s' % (_('Update down config file error'), traceback.format_exc()))
            finally:
                self.lock.release()
            print('%s[%s -> %s]: %s\n%s' % (_('Download Failed'),
                                            _task[0], _task[1], _url, traceback.format_exc()))
            time.sleep(1)
            return False


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))
