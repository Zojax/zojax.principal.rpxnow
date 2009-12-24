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
from zope.security.management import queryInteraction
from zope.app.security.interfaces import IAuthentication
from zope.app.container.interfaces import IObjectAddedEvent, IObjectRemovedEvent

from zojax.authentication.interfaces import ICredentialsPlugin

from interfaces import _, IOpenIdCredentials, IOpenIdUsersPlugin


class OpenIdCredentials(object):
    interface.implements(IOpenIdCredentials)

    failed = False
    principalInfo = None
    parameters = FieldProperty(IOpenIdCredentials['parameters'])

    def __init__(self, parameters):
        self.parameters = parameters

    @property
    def request(self):
        interaction = queryInteraction()

        if interaction is not None:
            for participation in interaction.participations:
                return participation


class CredentialsPlugin(Persistent):
    interface.implements(ICredentialsPlugin)

    def extractCredentials(self, request):
        """Tries to extract credentials from a request.

        A return value of None indicates that no credentials could be found.
        Any other return value is treated as valid credentials.
        """
        mode = request.get("openid.mode", None)

        if mode == "id_res":
            # id_res means 'positive assertion' in OpenID, more commonly
            # described as 'positive authentication'
            parameters = {}
            for field, value in request.form.iteritems():
                parameters[field] = value
            return OpenIdCredentials(parameters)

        elif mode == "cancel":
            # cancel is a negative assertion in the OpenID protocol,
            # which means the user did not authorize correctly.
            return None

        return None


@component.adapter(IOpenIdUsersPlugin, IObjectAddedEvent)
def installCredentialsPlugin(plugin, ev):
    auth = getUtility(IAuthentication)

    plugin = CredentialsPlugin()
    event.notify(ObjectCreatedEvent(plugin))

    auth = removeSecurityProxy(auth)
    if 'credendials.openid' in auth:
        del auth['credendials.openid']

    auth['credendials.openid'] = plugin
    auth.credentialsPlugins = tuple(auth.credentialsPlugins) + \
        ('credendials.openid',)


@component.adapter(IOpenIdUsersPlugin, IObjectRemovedEvent)
def uninstallCredentialsPlugin(plugin, ev):
    auth = getUtility(IAuthentication)

    plugins = list(auth.credentialsPlugins)
    if 'credendials.openid' in plugins:
        plugins.remove('credendials.openid')
        auth.credentialsPlugins = tuple(plugins)

    if 'credendials.openid' in auth:
        del auth['credendials.openid']
