#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2019 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import ssl
import m3u8
import json
import threading
import traceback
import subprocess
import time
from urllib.parse import urlparse
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.simple_queue import MemoryQueue
from HiveNetLib.simple_parallel import ParallelPool, ThreadParallel, ThreadParallelLock, ThreadParallelShareDict
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.lib.core import BaseDownDriverFW
from comics_down.down_driver.http_down_driver import HttpDownDriver


__MOUDLE__ = 'm3u8_downloader'  # 模块名
__DESCRIPT__ = u'm3u8视频下载模块'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.04.12'  # 发布日期


# 取消全局ssl验证
ssl._create_default_https_context = ssl._create_unverified_context


class M3u8DownLoader(object):
    """
    m3u8视频下载工具
    """

    def __init__(self, url: str, save_file: str, worker_num: int = 3, auto_retry: int = 0,
                 down_driver: BaseDownDriverFW = HttpDownDriver, down_extend_json: dict = {},
                 down_task_overtime: float = 0, **kwargs):
        """
        初始化下载工具

        @param {str} url - m3u8文件的下载地址（每次必须要送）
        @param {str} save_file - 下载文件的保存目录和文件名
        @param {int} worker_num=3 - 下载线程数量
        @param {int} auto_retry=0 - 自动重试次数
        @param {BaseDownDriverFW} down_driver=HttpDownDriver - 指定使用的下载驱动
        @param {dict} down_extend_json={} - 送入下载驱动的扩展参数，以下载驱动定义为准
        @param {float} down_task_overtime=0 - 下载任务的超时时间，超时视为失败
        @param {dict} kwargs - 可送入下载驱动的下载任务参数，以下载驱动定义为准
        """
        # 初始化参数
        self.url = url
        self.save_file = os.path.realpath(save_file)
        self.worker_num = worker_num
        self.auto_retry = auto_retry
        self.down_driver = down_driver
        self.down_extend_json = down_extend_json
        self.down_task_overtime = down_task_overtime
        self.kwargs = kwargs

        # 下载处理临时参数
        self._down_queue = MemoryQueue()  # 下载任务的队列
        self._lock = threading.RLock()
        self._down_path = os.path.split(self.save_file)[0]  # 文件保存目录
        self._temp_path = os.path.join(
            self._down_path, FileTool.get_file_name_no_ext(self.save_file)
        )  # 下载临时目录, 以无扩展名的文件名作为文件夹

        # 临时目录参数
        self._down_status_file = os.path.join(self._temp_path, 'down_status.json')  # 下载记录文件
        self._down_status = None
        self._m3u8_file = os.path.join(self._temp_path, 'playlist.m3u8')
        self._m3u8_url = self.url  # m3u8的真实下载地址（可能处理过程中会发生变化）
        self._list_file = os.path.join(self._temp_path, 'list.txt')  # 要下载的文件清单

    #############################
    # 公共工具函数
    #############################
    def download_m3u8_file(self):
        """
        下载m3u8文件
        """
        self.down_driver.download(
            self._m3u8_url, self._m3u8_file,
            extend_json=self.down_extend_json, **self.kwargs
        )

    def get_playlist(self):
        """
        获取播放文件清单

        @returns {tuple} - 返回 flist, key
            flist {list} - 下载文件清单
            keys {list} - 解密key信息列表, None代表无加密
        """
        flist = []
        keys = None

        # 检查要不要重新下载
        if not os.path.exists(self._m3u8_file):
            self.download_m3u8_file()

        # 借助第三方库解析文件
        _m3u8_obj = m3u8.load(self._m3u8_file)
        keys = _m3u8_obj.keys

        _base_url_info = urlparse(self._m3u8_url)
        if len(_m3u8_obj.files) == 0:
            # 文件中没有实际文件信息，需要根据信息获取新的url再下载真正的文件
            _new_url = _m3u8_obj.playlists[0].uri
            if not _new_url.startswith('http') and _new_url.startswith('/'):
                _new_url = '%s://%s/%s' % (
                    _base_url_info.scheme, _base_url_info.netloc, _new_url
                )
            else:
                _new_url = os.path.split(self._m3u8_url)[0] + '/' + _new_url

            # 重新下载
            FileTool.remove_file(self._m3u8_file)
            self._m3u8_url = _new_url
            self.down_driver.download(
                self._m3u8_url, self._m3u8_file,
                extend_json=self.down_extend_json, **self.kwargs
            )

            return self.get_playlist()

        # 解析文件
        for _file in _m3u8_obj.files:
            if _file.startswith('http://') or _file.startswith('https://'):
                _base_url_info = urlparse(_file)
                flist.append(_file)
            elif _file.find('/') < 0:
                # 只有文件名
                flist.append('%s://%s/%s/%s' % (
                    _base_url_info.scheme, _base_url_info.netloc,
                    os.path.split(_base_url_info.path)[0], _file
                ))
            else:
                # 有文件路径，缺域名
                flist.append('%s://%s/%s' % (
                    _base_url_info.scheme, _base_url_info.netloc, _file
                ))

        # 返回处理结果
        return flist, keys

    def merge_file(self):
        """
        合并视频文件
        """
        _call_para = {
            'shell': True, 'close_fds': True
        }
        if sys.platform == 'win32':
            _call_para['creationflags'] = subprocess.CREATE_NEW_CONSOLE

        _shell = subprocess.call(
            'ffmpeg -f concat -safe 0 -i "%s" -c copy "%s"' % (
                os.path.realpath(self._list_file), os.path.realpath(self.save_file)
            ), **_call_para
        )
        if _shell != 0:
            raise RuntimeError('merge file error')

    #############################
    # 处理函数
    #############################

    def start_download(self, re_write: bool = False):
        """
        启动下载处理

        @param {bool} re_write=False - 是否覆盖原有任务（重新下载）
        """
        # 清除已存在的所有临时文件
        if re_write:
            if os.path.exists(self.save_file):
                FileTool.remove_file(self.save_file)
            if os.path.exists(self._temp_path):
                FileTool.remove_dir(self._temp_path)
        elif os.path.exists(self.save_file):
            # 文件已存在，无需再次下载
            return {
                'status': 'existed'
            }

        # 加载下载状态文件
        self._down_status = self._get_down_status(auto_create=True)

        # 处理m3u8文件的文件列表
        if not os.path.exists(self._list_file):
            _flist, _keys = self.get_playlist()
            self._down_status['key'] = ''

            # 保存到list_file文件，用于后续合并
            with open(self._list_file, 'w') as f:
                for _file in _flist:
                    f.write('file %s\r\n' % (
                        os.path.join(
                            self._temp_path, os.path.split(_file)[1]
                        ).replace('\\', '/')
                    ))
                    self._down_status['files'][_file] = 'downloading'  # 登记到状态表

            self._save_down_status(self._down_status)

        # 执行下载操作
        self._download()

    #############################
    # 内部函数-下载状态文件处理
    #############################

    def _get_down_status(self, auto_create: bool = False) -> dict:
        """
        从磁盘装载下载进展并返回

        @param {bool} auto_create=False - 文件不存在是否自动创建

        @returns {dict} - 当前下载状态字典
            {
                'status': 'downloading',  # 下载状态，downloading-正在下载，done-已完成，failed-失败, existed-文件已存在
                'files': {},
                'key': ''  # 秘钥
            }
        """
        if os.path.exists(self._down_status_file):
            with open(self._down_status_file, 'rb') as f:
                _json = str(f.read(), encoding='utf-8')
                _down_status = json.loads(_json)
        else:
            _down_status = {
                'status': 'downloading',
                'files': {},
                'key': ''
            }
            if auto_create:
                # 自动创建
                FileTool.create_dir(self._temp_path, exist_ok=True)
                self._save_down_status(_down_status)

        return _down_status

    def _save_down_status(self, down_status: dict):
        """
        保存下载状态文件

        @param {dict} down_status - 当前状态字典
        """
        _json = json.dumps(down_status, ensure_ascii=False, indent=2)
        with open(self._down_status_file, 'wb') as f:
            f.write(str.encode(_json, encoding='utf-8'))

    #############################
    # 内部函数-下载操作
    #############################
    def _download(self):
        """
        多线程下载文件
        """
        # 装载下载清单
        self._down_queue.clear()
        for _file in self._down_status['files'].keys():
            if self._down_status['files'][_file] != 'done':
                self._down_queue.put(_file)

        # 创建进程池
        _pool = ParallelPool(
            deal_fun=self._down_worker_fun,
            parallel_class=ThreadParallel,
            run_args=(self._down_queue, ),
            task_queue=self._down_queue,
            maxsize=int(self.worker_num),
            worker_overtime=float(self.down_task_overtime),
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

        # 检查是否全部完成了
        for _file in self._down_status['files'].keys():
            if self._down_status['files'][_file] != 'done':
                raise RuntimeError('not finished')

        # 全部完成了，合并文件
        self.merge_file()

        # 合并成功，删除临时目录
        FileTool.remove_dir(self._temp_path)

    def _down_worker_fun(self, q, ):
        """
        下载工作函数
        """
        _url = ''

        try:
            _url = q.get(block=False)
        except:
            # 没有取到任务
            time.sleep(0.5)
            return None

        try:
            _file_name = os.path.split(_url)[1]

            _retry_time = 0
            while True:
                try:
                    self.down_driver.download(
                        _url, os.path.join(self._temp_path, _file_name),
                        extend_json=self.down_extend_json, **self.kwargs
                    )
                    break  # 下载成功退出
                except:
                    if _retry_time <= self.auto_retry:
                        _retry_time += 1
                        continue
                    else:
                        raise

            # 下载成功，更新下载结果
            self._lock.acquire()
            try:
                self._down_status['files'][_url] = 'done'
                self._save_down_status(self._down_status)
            finally:
                self._lock.release()

            return True
        except:
            # 下载失败
            print('Download error: %s' % _url)
            print(traceback.format_exc())
            time.sleep(0.5)
            return False


if __name__ == '__main__':
    # 当程序自己独立运行时执行的操作
    # 打印版本信息
    print(('模块名：%s  -  %s\n'
           '作者：%s\n'
           '发布日期：%s\n'
           '版本：%s' % (__MOUDLE__, __DESCRIPT__, __AUTHOR__, __PUBLISH__, __VERSION__)))
