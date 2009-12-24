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

from openid.consumer.consumer import Consumer
from openid.extensions.sreg import SRegRequest

from zojax.statusmessage.interfaces import IStatusMessage
from zojax.authentication.interfaces import ILoginService

from zojax.principal.openid.interfaces import _, IOpenIdAuthenticator
from zojax.principal.openid.plugin import \
    SESSION_KEY, getReturnToURL, normalizeIdentifier


class OpenIdSignIn(object):

    def __call__(self):
        request = self.request
        siteURL = u'%s/'%absoluteURL(getSite(), request)

        if not IUnauthenticatedPrincipal.providedBy(request.principal):
            request.response.redirect(siteURL)
            return u''

        if not 'openid_form_submitted' in request:
            request.response.redirect(siteURL)
            return u''

        identifier = request.get('openid_identifier')
        if not identifier:
            IStatusMessage(request).add(
                _(u"Please specify your OpenID identifier."))
            request.response.redirect(siteURL)
            return u''

        authenticator = getUtility(IOpenIdAuthenticator)
        session = ISession(request)[SESSION_KEY]
        consumer = Consumer(session, authenticator.store)

        try:
            authRequest = consumer.begin(identifier)
            redirectURL = authRequest.redirectURL(
                siteURL, getReturnToURL(request))
        except Exception, err:
            IStatusMessage(request).add(err, 'error')
            redirectURL = siteURL

        request.response.redirect(redirectURL)
        return u''


class CompleteOpenIdSignIn(object):

    def __call__(self):
        self.request.response.redirect(
            u'%s/successOpenIdSignIn?processed=1'%absoluteURL(
                getSite(), self.request))
        return u''


class SuccessOpenIdSignIn(object):

    def __call__(self, *args, **kw):
        request = self.request
        principal = request.principal
        auth = getUtility(IAuthentication)

        if IUnauthenticatedPrincipal.providedBy(principal):
            msg = auth.loginMessage
            if not msg:
                msg = _('Login failed.')

            IStatusMessage(request).add(msg, 'warning')

            request.response.redirect(
                u'%s/login.html'%absoluteURL(getSite(), request))
        elif 'processed' in request:
            if getMultiAdapter((auth, request), ILoginService).success():
                return

        request.response.redirect(u'%s/'%absoluteURL(getSite(), request))
        return u''
