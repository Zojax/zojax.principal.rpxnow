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
from zope import component
from zope.component import getUtility, getMultiAdapter
from zope.session.interfaces import ISession
from zope.traversing.browser import absoluteURL
from zope.app.component.hooks import getSite
from zope.app.security.interfaces import \
    IAuthentication, IUnauthenticatedPrincipal

from zojax.statusmessage.interfaces import IStatusMessage

from zojax.principal.rpxnow.interfaces import _
from zojax.principal.rpxnow.plugin import SESSION_KEY


class RPXNowSignIn(object):

    def __call__(self):
        request = self.request
        siteURL = u'%s/'%absoluteURL(getSite(), request)

        if not IUnauthenticatedPrincipal.providedBy(request.principal):
            request.response.redirect(siteURL)
            return u''

        if not 'token' in request:
            request.response.redirect(siteURL)
            return u''

        token = request.get('token')
        if not token:
            IStatusMessage(request).add(
                _(u"Please specify your token."))
            request.response.redirect(siteURL)
            return u''
        session = ISession(request)[SESSION_KEY]['token'] = token
        request.response.redirect(siteURL)
        return u''
