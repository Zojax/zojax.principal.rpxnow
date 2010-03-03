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
from zope.session.interfaces import ISession

from zojax.authentication.interfaces import ICredentialsPlugin
from zojax.authentication.factory import CredentialsPluginFactory

from interfaces import _, SESSION_KEY, IRPXNowCredentials, IRPXNowUsersPlugin, IRPXNowAuthenticationProduct


class RPXNowCredentials(object):
    interface.implements(IRPXNowCredentials)

    token = None

    def __init__(self, token):
        self.token = token


class CredentialsPlugin(Persistent):
    interface.implements(ICredentialsPlugin)

    def extractCredentials(self, request):
        """Tries to extract credentials from a request.

        A return value of None indicates that no credentials could be found.
        Any other return value is treated as valid credentials.
        """
        token = ISession(request)[SESSION_KEY].get('token')
        if not token:
            token = request.get('token')
            if token:
                ISession(request)[SESSION_KEY]['token'] = token
                return RPXNowCredentials(token)
            return None
        return RPXNowCredentials(token)
    

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
    if 'credentials.rpxnow' in auth:
        del auth['credentials.rpxnow']

    auth['credentials.rpxnow'] = plugin
    auth.credentialsPlugins = tuple(auth.credentialsPlugins) + \
        ('credentials.rpxnow',)


@component.adapter(IRPXNowUsersPlugin, IObjectRemovedEvent)
def uninstallCredentialsPlugin(plugin, ev):
    auth = getUtility(IAuthentication)

    plugins = list(auth.credentialsPlugins)
    if 'credentials.rpxnow' in plugins:
        plugins.remove('credentials.rpxnow')
        auth.credentialsPlugins = tuple(plugins)

    if 'credentials.rpxnow' in auth:
        del auth['credentials.rpxnow']
