##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id$
"""
import urllib
from zope.component import getUtility
from zope.traversing.browser import absoluteURL
from zope.app.component.hooks import getSite

from zojax.principal.rpxnow.interfaces import IRPXNowAuthenticationProduct

class LoginAction(object):

    id = u'rpxnow.login'
    order = 30

    def update(self):
        siteURL = absoluteURL(getSite(), self.request)
        self.successUrl = '%s/login-success.html'%siteURL
        self.signInLink = 'https://zojax-eval.rpxnow.com/openid/v2/signin?%s' % \
                        urllib.urlencode(dict(token_url='%s/rpxNowSignIn'%siteURL))

    def isProcessed(self):
        return False
