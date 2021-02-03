#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
http代理，用于屏蔽网站对selenium的检测，或者收集网页信息
启动命令：mitmdump -s http_proxy.py -p 9000
@module http_proxy
@file http_proxy.py
"""

import re
from mitmproxy import ctx, http

injected_javascript = '''
// overwrite the `languages` property to use a custom getter
Object.defineProperty(navigator, "languages", {
  get: function() {
    return ["zh-CN","zh","zh-TW","en-US","en"];
  }
});
// Overwrite the `plugins` property to use a custom getter.
Object.defineProperty(navigator, 'plugins', {
  get: () => [1, 2, 3, 4, 5],
});
// Pass the Webdriver test
Object.defineProperty(navigator, 'webdriver', {
  get: () => false,
});
// Pass the Chrome Test.
// We can mock this in as much depth as we need for the test.
window.navigator.chrome = {
  runtime: {},
  // etc.
};
// Pass the Permissions Test.
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
  parameters.name === 'notifications' ?
    Promise.resolve({ state: Notification.permission }) :
    originalQuery(parameters)
);
'''


def response(flow):
    # Only process 200 responses of HTML content.
    if not flow.response.status_code == 200:
        return

    # Inject a script tag containing the JavaScript.
    html = flow.response.text
    html = html.replace('<head>', '<head><script>%s</script>' % injected_javascript)
    flow.response.text = str(html.replace('devtoolsDetector', '###'))
    ctx.log.info('插入成功 ')


# def response(flow):
#     """修改应答数据"""
#     # 屏蔽selenium检测
#     # for webdriver_key in ['webdriver', '__driver_evaluate', '__webdriver_evaluate', '__selenium_evaluate', '__fxdriver_evaluate', '__driver_unwrapped', '__webdriver_unwrapped', '__selenium_unwrapped', '__fxdriver_unwrapped', '_Selenium_IDE_Recorder', '_selenium', 'calledSelenium', '_WEBDRIVER_ELEM_CACHE', 'ChromeDriverw', 'driver-evaluate', 'webdriver-evaluate', 'selenium-evaluate', 'webdriverCommand', 'webdriver-evaluate-response', '__webdriverFunc', '__webdriver_script_fn', '__$webdriverAsyncExecutor', '__lastWatirAlert', '__lastWatirConfirm', '__lastWatirPrompt', '$chrome_asyncScriptInfo', '$cdc_asdjflasutopfhvcZLmcfl_']:
#     #     ctx.log.info('Remove"{}"from{}.'.format(webdriver_key, flow.request.url))
#     #     flow.response.text = flow.response.text.replace(
#     #         '"{}"'.format(webdriver_key), '"NO-SUCH-ATTR"')
#     #     flow.response.text = flow.response.text.replace('t.webdriver', 'false')
#     #     flow.response.text = flow.response.text.replace('ChromeDriver', '')
#     flow.response.text = flow.response.text.replace('webdriver', 'userAgent')
