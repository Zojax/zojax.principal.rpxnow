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
from zope.location import Location
from zope.component import getUtility
from zope.proxy import removeAllProxies
from zope.exceptions.interfaces import UserError
from zope.cachedescriptors.property import Lazy
from zope.session.interfaces import ISession
from zope.traversing.browser import absoluteURL
from zope.app.component.hooks import getSite
from zope.app.container.btree import BTreeContainer
from zope.app.container.interfaces import DuplicateIDError
from zope.app.container.interfaces import INameChooser, IObjectRemovedEvent
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.app.authentication.interfaces import IFoundPrincipalFactory

from rpxnow.extensions.sreg import SRegResponse
from rpxnow.consumer.consumer import Consumer, SuccessResponse

from zojax.authentication.factory import AuthenticatorPluginFactory
from zojax.authentication.interfaces import PrincipalRemovingEvent
from zojax.authentication.interfaces import PrincipalInitializationFailed
from zojax.statusmessage.interfaces import IStatusMessage
from zojax.principal.registration.interfaces import IPortalRegistration

from zojax.principal.rpxnow.interfaces import _, IRpxNowPrincipal
from zojax.principal.rpxnow.interfaces import \
    IRpxNowCredentials, IRpxNowUsersPlugin, IRpxNowPrincipalInfo
from zojax.principal.rpxnow.store import ZopeStore

SESSION_KEY = 'zojax.principal.rpxnow'
CHALLENGE_INITIATED_MARKER = '_rpxnow_challenge_initiated'


class RpxNowPrincipal(Persistent, Location):
    interface.implements(IRpxNowPrincipal)

    @property
    def title(self):
        return u'rpxnow%s'%self.__name__

    @Lazy
    def id(self):
        self.id = '%s%s%s'%(getUtility(IAuthentication).prefix,
                            self.__parent__.prefix, self.__name__)
        return self.id


class RpxNowPrincipalInfo(object):
    interface.implements(IRpxNowPrincipalInfo)

    description = u''

    def __init__(self, id, internal):
        self.id = id
        self.identifier = internal.identifier
        self.title = internal.title
        self.internalId = internal.__name__

    def __repr__(self):
        return 'RpxNowPrincipalInfo(%r)' % self.id


def getReturnToURL(request):
    return absoluteURL(getSite(), request) + '/@@completeRpxNowSignIn'


def normalizeIdentifier(identifier):
    identifier = identifier.lower()

    if not identifier.startswith('http://') and \
            not identifier.startswith('https://'):
        identifier = 'http://' + identifier

    if not identifier.endswith('/'):
        identifier = identifier + '/'

    return unicode(identifier)


class AuthenticatorPlugin(BTreeContainer):
    interface.implements(IRpxNowUsersPlugin, INameChooser)

    def __init__(self, prefix=u'zojax.rpxnow.'):
        self.store = ZopeStore()
        self.prefix = unicode(prefix)
        self.__name_chooser_counter = 1
        self.__id_by_identifier = self._newContainerData()

        super(AuthenticatorPlugin, self).__init__()

    def authenticateCredentials(self, credentials):
        """Authenticates credentials.

        If the credentials can be authenticated, return an object that provides
        IPrincipalInfo. If the plugin cannot authenticate the credentials,
        returns None.
        """
        if not IRpxNowCredentials.providedBy(credentials):
            return None

        if credentials.failed:
            return None

        if credentials.principalInfo is not None \
                and credentials.principalInfo.internalId in self:
            return credentials.principalInfo

        request = credentials.request

        consumer = Consumer(ISession(request)[SESSION_KEY], self.store)

        returnto = credentials.parameters.get(
            'rpxnow.return_to', getReturnToURL(request))
        response = consumer.complete(
            credentials.parameters, returnto.split('?')[0])

        if isinstance(response, SuccessResponse):
            identifier = normalizeIdentifier(response.identity_url)
            principalId = self.getPrincipalByRpxNowIdentifier(identifier)
            if principalId is None:
                # Principal does not exist
                principal = RpxNowPrincipal()
                principal.identifier = identifier

                sregResponse = SRegResponse.fromSuccessResponse(response)

                name = INameChooser(self).chooseName('', principal)
                self[name] = principal
                principalId = self.getPrincipalByRpxNowIdentifier(identifier)

                # register principal in portal registration tool
                auth = getUtility(IAuthentication)
                pid = auth.prefix + self.prefix + name
                try:
                    principal = auth.getPrincipal(pid)
                    getUtility(IPortalRegistration).registerPrincipal(principal)
                except PrincipalLookupError:
                    pass

            principalInfo = self.principalInfo(self.prefix + principalId)
            credentials.principalInfo = principalInfo
            return principalInfo

        else:
            raise PrincipalInitializationFailed(response.message)

        return None

    def principalInfo(self, id):
        """Returns an IPrincipalInfo object for the specified principal id.

        If the plugin cannot find information for the id, returns None.
        """
        if id.startswith(self.prefix):
            internal = self.get(id[len(self.prefix):])
            if internal is not None:
                return RpxNowPrincipalInfo(id, internal)

    def getPrincipalByRpxNowIdentifier(self, identifier):
        """ return principal info by RpxNow Identifier """
        if identifier in self.__id_by_identifier:
            return self.__id_by_identifier.get(identifier)

    def checkName(self, name, object):
        if not name:
            raise UserError(
                "An empty name was provided. Names cannot be empty.")

        if isinstance(name, str):
            name = unicode(name)
        elif not isinstance(name, unicode):
            raise TypeError("Invalid name type", type(name))

        if not name.isdigit():
            raise UserError("Name must consist of digits.")

        if name in self:
            raise UserError("The given name is already being used.")

        return True

    def chooseName(self, name, object):
        while True:
            name = unicode(self.__name_chooser_counter)
            try:
                self.checkName(name, object)
                return name
            except UserError:
                self.__name_chooser_counter += 1

    def __setitem__(self, id, principal):
        # A user with the identifier already exists
        identifier = principal.identifier
        if identifier in self.__id_by_identifier:
            raise DuplicateIDError(
                'Principal Identifier already taken!, ' + identifier)

        super(AuthenticatorPlugin, self).__setitem__(id, principal)

        self.__id_by_identifier[principal.identifier] = id

    def __delitem__(self, id):
        # notify about principal removing
        internal = self[id]

        auth = getUtility(IAuthentication)
        info = RpxNowPrincipalInfo(self.prefix+id, internal)
        info.credentialsPlugin = None
        info.authenticatorPlugin = self
        principal = IFoundPrincipalFactory(info)(auth)
        principal.id = auth.prefix + self.prefix + id
        event.notify(PrincipalRemovingEvent(principal))

        # actual remove
        super(AuthenticatorPlugin, self).__delitem__(id)

        del self.__id_by_identifier[internal.identifier]


@component.adapter(IRpxNowUsersPlugin, IObjectRemovedEvent)
def pluginRemovedHandler(plugin, event):
    plugin = removeAllProxies(plugin)

    for id in plugin:
        del plugin[id]


authenticatorFactory = AuthenticatorPluginFactory(
    "principal.rpxnow", AuthenticatorPlugin, ((IRpxNowUsersPlugin, ''),),
    _(u'RpxNow plugin'),
    _(u'This plugin allow use rpxnow login '
      u'like google, yahoo, lifejournal and many others'))
