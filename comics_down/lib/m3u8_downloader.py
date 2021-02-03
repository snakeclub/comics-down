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
# 根据当前文件路径将包路径纳入，在非安装的情况下可以引用到
sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
from comics_down.down_driver.init_aria2 import Aria2Driver


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
    def get_play_lists(cls, url, temp_save_file, is_resume=False, exists_no_down=False):
        """
        从m3u8获取下载文件列表

        @param {str} url - m3u8文件的url
        @param {str} temp_save_file - 临时保存的文件
        @param {bool} is_resume=False - 是否自动重试
        @param {bool} exists_no_down=False - 如果文件已存在无需再下载

        @return {tuple} - 返回 flist, key
            flist {list} - 下载文件清单
            key {str} - 解密key
        """
        flist = []
        key = ''

        print('m3u8_url: %s' % url)
        if exists_no_down and os.path.exists(temp_save_file):
            print('m3u8 file exists: %s' % temp_save_file)
        else:
            if os.path.exists(temp_save_file):
                FileTool.remove_file(temp_save_file)

            NetTool.download_http_file(
                url, filename=temp_save_file, is_resume=is_resume,
                headers={'User-agent': 'Mozilla/5.0'},
                connect_timeout=20, verify=False
            )

        _m3u8_obj = m3u8.load(temp_save_file)

        _base_url_info = urlparse(url)
        if len(_m3u8_obj.files) == 0:
            # 进行一次跳转
            _new_url = _m3u8_obj.playlists[0].uri
            if not _new_url.startswith('http') and _new_url.startswith('/'):
                _new_url = '%s://%s/%s' % (
                    _base_url_info.scheme, _base_url_info.netloc, _new_url
                )
            else:
                _new_url = os.path.split(url)[0]+'/' + _new_url

            print('new url: %s' % _new_url)
            return cls.get_play_lists(_new_url, temp_save_file)

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

        print('\n'.join(flist))
        return flist, key

    @classmethod
    def hand_download(cls, save_file, url):
        """
        手工下载m3u8操作

        @param {str} save_file - 要保存的文件名
        @param {str} url - m3u8的url地址
        """
        # 保存路径
        _path = os.path.split(save_file)[0]
        _temp_path = os.path.join(
            _path, FileTool.get_file_name_no_ext(save_file)
        )
        FileTool.create_dir(_temp_path, exist_ok=True)
        _list_file = os.path.join(_temp_path, 'list.txt')

        if not os.path.exists(_list_file):
            # 下载m3u8文件并生成合并文件
            _flielist, _key = cls.get_play_lists(
                url, os.path.join(_temp_path, 'index.m3u8'), is_resume=True, exists_no_down=True
            )

            # 生成合并文件
            with open(_list_file, 'w', encoding='utf-8') as f:
                for _file in _flielist:
                    f.write('file %s\r\n' % (
                        os.path.join(
                            _temp_path, os.path.split(_file)[1]
                        ).replace('\\', '/')
                    ))

        # 检查文件是否齐全
        with open(_list_file, 'r', encoding='utf-8') as f:
            _lines = f.readlines()
            for _line in _lines:
                _line = _line.strip()
                if _line != '' and not os.path.exists(_line[5:]):
                    print('%s not exists!' % _line)
                    return

        # 全部完成了，合并文件
        _shell = subprocess.call('ffmpeg -f concat -safe 0 -i "%s" -c copy "%s"' % (
            os.path.realpath(_list_file), os.path.realpath(save_file)
        ))
        if _shell != 0:
            raise RuntimeError('merge error')

        # 合并成功，删除临时目录
        FileTool.remove_dir(_temp_path)

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
            # NetTool.download_http_file(
            #     _url, filename=os.path.join(self.temp_path, _file_name),
            #     is_resume=self.is_resume,
            #     headers={'User-agent': 'Mozilla/5.0'},
            #     connect_timeout=30, verify=False, retry=self.retry, show_rate=True
            # )

            _para_dict = {
                'down_overtime': '600'
            }
            Aria2Driver.download(
                _url, os.path.join(self.temp_path, _file_name), **_para_dict
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


    # M3u8Downloader.get_play_lists(
    #     url='https://xxx/index.m3u8',
    #     temp_save_file=r'D:\test_m3u8\test\playlist.m3u8',
    #     is_resume=True, exists_no_down=True
    # )
    # playlist.m3u8
    # M3u8Downloader.hand_download(
    #     r'E:\m3u8\xxx.mp4',
    #     'https://xxx/index.m3u8'
    # )

    M3u8Downloader(
        r'xxx.mp4', 'https://xxx/index.m3u8',
        process_num=3, is_resume=True, retry=3
    )
