#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Copyright 2018 黎慧剑
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
selenium伪装代理，用于屏蔽网站对selenium的检测
注：某些网站会检测客户端，如果是开发模式会屏蔽内容，需要通过代理进行欺骗
启动命令：mitmdump -s selenium_feign_proxy.py -p 9000

@module selenium_feign_proxy
@file selenium_feign_proxy.py
"""

from mitmproxy import ctx

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
