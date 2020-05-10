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
import threading
import traceback
import subprocess
import time
from urllib.parse import urlparse
from HiveNetLib.base_tools.file_tool import FileTool
from HiveNetLib.base_tools.net_tool import NetTool
from HiveNetLib.simple_queue import MemoryQueue
from HiveNetLib.simple_parallel import ParallelPool, ThreadParallel, ThreadParallelLock, ThreadParallelShareDict


__MOUDLE__ = 'm3u8_downloader'  # 模块名
__DESCRIPT__ = u'm3u8视频下载模块'  # 模块描述
__VERSION__ = '0.1.0'  # 版本
__AUTHOR__ = u'黎慧剑'  # 作者
__PUBLISH__ = '2020.04.12'  # 发布日期


# 取消全局ssl验证
ssl._create_default_https_context = ssl._create_unverified_context


class M3u8Downloader(object):
    """
    m3u8下载器
    """

    #############################
    # 静态函数
    #############################
    @classmethod
    def get_play_lists(cls, url, temp_save_file):
        """
        从m3u8获取下载文件列表

        @param {str} url - m3u8文件的url
        @param {str} temp_save_file - 临时保存的文件

        @return {tuple} - 返回 flist, key
            flist {list} - 下载文件清单
            key {str} - 解密key
        """
        flist = []
        key = ''

        NetTool.download_http_file(
            url, filename=temp_save_file, is_resume=False,
            headers={'User-agent': 'Mozilla/5.0'},
            connect_timeout=20, verify=False
        )

        _m3u8_obj = m3u8.load(temp_save_file)

        _base_url_info = urlparse(url)
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

        return flist, key

    #############################
    # 构造函数
    #############################
    def __init__(self, save_file: str, url: str, process_num=5, is_resume=True, retry=0):
        """
        构造函数（直接下载文件）

        @param {str} save_file - 保存的文件,例如 'd:/down/1.mp4'
        @param {str} url - m3u8文件的url
        @param {int} process_num=5 - 下载线程数量
        @param {bool} is_resume=True - 是否使用断点续传
        @param {int} retry=0 - 自动重试次数

        """
        self.down_queue = MemoryQueue()  # 下载任务的队列
        self.lock = threading.RLock()
        self.save_file = save_file
        self.process_num = process_num
        self.is_resume = is_resume
        self.retry = retry
        self.down_path = os.path.split(save_file)[0]  # 文件保存目录
        self.temp_path = os.path.join(
            self.down_path, FileTool.get_file_name_no_ext(save_file)
        )  # 下载临时目录
        # 创建目录
        FileTool.create_dir(self.temp_path, exist_ok=True)
        self.down_status_file = os.path.join(self.temp_path, 'down_status.json')
        self.down_status = None
        self.list_file = os.path.join(self.temp_path, 'list.txt')

        # 获取已下载进度
        self._load_down_status()
        if self.down_status is None:
            # 获取m3u8信息
            self.down_status = {
                'files': {},
                'key': ''  # 秘钥
            }

            _flielist, self.down_status['key'] = self.get_play_lists(
                url, os.path.join(self.temp_path, 'playlist.m3u8')
            )

            with open(self.list_file, 'w') as f:
                for _file in _flielist:
                    f.write('file %s\r\n' % (
                        os.path.join(
                            self.temp_path, os.path.split(_file)[1]
                        ).replace('\\', '/')
                    ))
                    self.down_status['files'][_file] = 'downloading'

            # 保存状态
            self._save_down_status()

        # 启动下载处理
        self._download()

    #############################
    # 内部函数
    #############################
    def _save_down_status(self):
        """
        保存下载进展到磁盘
        """
        _json = str(self.down_status)
        with open(self.down_status_file, 'wb') as f:
            f.write(str.encode(_json, encoding='utf-8'))

    def _load_down_status(self):
        """
        从磁盘装载下载进展
        """
        if os.path.exists(self.down_status_file):
            with open(self.down_status_file, 'rb') as f:
                _eval = str(f.read(), encoding='utf-8')
                self.down_status = eval(_eval)

    def _download(self):
        """
        多线程下载文件

        """
        # 装载下载清单
        self.down_queue.clear()
        for _file in self.down_status['files'].keys():
            if self.down_status['files'][_file] != 'done':
                self.down_queue.put(_file)

        # 创建进程池
        _pool = ParallelPool(
            deal_fun=self._down_worker_fun,
            parallel_class=ThreadParallel,
            run_args=(self.down_queue, ),
            task_queue=self.down_queue,
            maxsize=int(self.process_num),
            worker_overtime=float(3000),
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
        for _file in self.down_status['files'].keys():
            if self.down_status['files'][_file] != 'done':
                raise RuntimeError('not finished')

        # 全部完成了，合并文件
        _shell = subprocess.call('ffmpeg -f concat -safe 0 -i "%s" -c copy "%s"' % (
            os.path.realpath(self.list_file), os.path.realpath(self.save_file)
        ))
        if _shell != 0:
            raise RuntimeError('merge error')

        # 合并成功，删除临时目录
        FileTool.remove_dir(self.temp_path)

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

            # 下载文件
            NetTool.download_http_file(
                _url, filename=os.path.join(self.temp_path, _file_name),
                is_resume=self.is_resume,
                headers={'User-agent': 'Mozilla/5.0'},
                connect_timeout=30, verify=False, retry=self.retry, show_rate=True
            )

            # 下载成功，更新下载结果
            self.lock.acquire()
            try:
                self.down_status['files'][_url] = 'done'
                self._save_down_status()
            finally:
                self.lock.release()

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

    # M3u8Downloader(
    #     'd:/myfile.mp4', 'https://www7.laqddcc.com/hls/2019/11/26/OXUon3vn/playlist.m3u8',
    #     process_num=1, is_resume=False
    # )
    url = 'https://cdn-1.kkp2p.com/hls/2019/06/23/82pQs9yn/playlist.m3u8'
    _base_url_info = urlparse(url)
    print(
        '%s://%s/%s/%s' % (
            _base_url_info.scheme, _base_url_info.netloc,
            os.path.split(_base_url_info.path)[0], 'haha.ts'
        )
    )
