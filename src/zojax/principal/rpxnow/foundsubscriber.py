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
from zope import interface, component
from zope.component import getUtility
from zope.security.management import queryInteraction
from zope.app.security.interfaces import IAuthentication
from zope.app.authentication.interfaces import IFoundPrincipalCreated
from zope.app.authentication.interfaces import IPluggableAuthentication
from zope.security.management import queryInteraction
from zope.session.interfaces import ISession

from zojax.authentication.interfaces import IPrincipalLoggingOutEvent

from interfaces import IRPXNowPrincipal, IRPXNowPrincipalMarker
from interfaces import IRPXNowPrincipalInfo, IRPXNowUsersPlugin
from interfaces import IRPXNowAuthenticationProduct, SESSION_KEY


@component.adapter(IFoundPrincipalCreated)
def foundPrincipalCreated(event):
    info = event.info

    if IRPXNowPrincipalInfo.providedBy(event.info):
        principal = event.principal
        principal.identifier = info.identifier
        principal.title = info.title
        principal.description = u''
        interface.alsoProvides(principal, IRPXNowPrincipalMarker)


@component.adapter(IRPXNowPrincipalMarker)
@interface.implementer(IRPXNowPrincipal)
def getInternalPrincipal(principal):
    auth = IPluggableAuthentication(getUtility(IAuthentication), None)

    if auth is not None:
        id = principal.id

        if id.startswith(auth.prefix):
            id = id[len(auth.prefix):]

            for name, plugin in auth.getAuthenticatorPlugins():
                if IRPXNowUsersPlugin.providedBy(plugin):
                    if id.startswith(plugin.prefix):
                        id = id[len(plugin.prefix):]
                        return plugin[id]


@component.adapter(IPrincipalLoggingOutEvent)
def principalLoggingOut(event):
    if IRPXNowPrincipalMarker.providedBy(event.principal):
        request = None
        interaction = queryInteraction()

        if interaction is not None:
            for participation in interaction.participations:
                request =  participation
        if request is not None:
            ISession(request)[SESSION_KEY]['token'] = None