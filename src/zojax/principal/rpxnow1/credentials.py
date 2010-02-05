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
from persistent import Persistent

from zope import interface, component, event
from zope.component import getUtility
from zope.lifecycleevent import ObjectCreatedEvent
from zope.schema.fieldproperty import FieldProperty
from zope.security.proxy import removeSecurityProxy
from zope.app.security.interfaces import IAuthentication
from zope.app.container.interfaces import IObjectAddedEvent, IObjectRemovedEvent

from zojax.authentication.interfaces import ICredentialsPlugin
from zojax.authentication.factory import CredentialsPluginFactory

from interfaces import _, IRPXNowCredentials, IRPXNowUsersPlugin, IRPXNowAuthenticationProduct


class RPXNowCredentials(object):
    interface.implements(IRPXNowCredentials)

    fcauth = None

    def __init__(self, fcauth):
        self.fcauth = fcauth


class CredentialsPlugin(Persistent):
    interface.implements(ICredentialsPlugin)

    def extractCredentials(self, request):
        """Tries to extract credentials from a request.

        A return value of None indicates that no credentials could be found.
        Any other return value is treated as valid credentials.
        """
        product = getUtility(IRPXNowAuthenticationProduct)
        cookie = request.getCookies().get(product.cookieNames[0])

        if cookie:
            return RPXNowCredentials(cookie)

        return None


credentialsFactory = CredentialsPluginFactory(
    "credentials.rpxnow", CredentialsPlugin, (),
    _(u'RPX Now credentials plugin'),
    u'')


@component.adapter(IRPXNowUsersPlugin, IObjectAddedEvent)
def installCredentialsPlugin(plugin, ev):
    auth = getUtility(IAuthentication)

    plugin = CredentialsPlugin()
    event.notify(ObjectCreatedEvent(plugin))

    auth = removeSecurityProxy(auth)
    if 'credendials.rpxnow' in auth:
        del auth['credendials.rpxnow']

    auth['credendials.rpxnow'] = plugin
    auth.credentialsPlugins = tuple(auth.credentialsPlugins) + \
        ('credendials.rpxnow',)


@component.adapter(IRPXNowUsersPlugin, IObjectRemovedEvent)
def uninstallCredentialsPlugin(plugin, ev):
    auth = getUtility(IAuthentication)

    plugins = list(auth.credentialsPlugins)
    if 'credendials.rpxnow' in plugins:
        plugins.remove('credendials.rpxnow')
        auth.credentialsPlugins = tuple(plugins)

    if 'credendials.rpxnow' in auth:
        del auth['credendials.rpxnow']
