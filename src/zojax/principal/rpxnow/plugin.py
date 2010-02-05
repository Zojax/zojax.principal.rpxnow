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
import logging
import urllib
import simplejson
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

from zojax.cache.interfaces import ICacheConfiglet
from zojax.authentication.factory import AuthenticatorPluginFactory
from zojax.authentication.interfaces import PrincipalRemovingEvent
from zojax.authentication.interfaces import PrincipalInitializationFailed
from zojax.statusmessage.interfaces import IStatusMessage
from zojax.principal.registration.interfaces import IPortalRegistration

from interfaces import _, IRPXNowPrincipal
from interfaces import \
    IRPXNowCredentials, IRPXNowUsersPlugin, IRPXNowPrincipalInfo, \
    IRPXNowAuthenticationProduct, SESSION_KEY

logger = logging.getLogger('zojax.principal.rpxnow')
_marker = object()


class RPXNowPrincipal(Persistent, Location):
    interface.implements(IRPXNowPrincipal)

    @Lazy
    def id(self):
        self.id = '%s%s%s'%(getUtility(IAuthentication).prefix,
                            self.__parent__.prefix, self.__name__)
        return self.id


class RPXNowPrincipalInfo(object):
    interface.implements(IRPXNowPrincipalInfo)

    description = u''

    def __init__(self, id, internal):
        self.id = id
        self.identifier = internal.identifier
        self.title = internal.title
        self.internalId = internal.__name__

    def __repr__(self):
        return 'RPXNowPrincipalInfo(%r)' % self.id


class AuthenticatorPlugin(BTreeContainer):
    interface.implements(IRPXNowUsersPlugin, INameChooser)

    def __init__(self, prefix=u'zojax.rpxnow.'):
        self.prefix = unicode(prefix)
        self.__name_chooser_counter = 1
        self.__id_by_identifier = self._newContainerData()

        super(AuthenticatorPlugin, self).__init__()

    def _getRPXNowUserInfo(self, token):
        product = component.getUtility(IRPXNowAuthenticationProduct)
        cache = component.getUtility(ICacheConfiglet, context=self)
        ob = ('zojax.principal.rpxnow', '_getRPXNowUserInfo')
        key = {'token': token}
        result = cache.query(ob, key, _marker)
        if result is _marker or not result:
            params = {
              "apiKey" : product.apiKey,
              "token" : token,
              "format" : "json",
            }
            try:
                result = simplejson.loads(urllib.urlopen('%s/auth_info'%product.rpcURL, urllib.urlencode(params)).read())
                if result['stat'] != 'ok':
                    return False
                else:
                    result = result['profile']
            except:
                logger.exception("Problem getting the response")
                return False
            cache.set(result, ob, key)
        return result

    def authenticateCredentials(self, credentials):
        """Authenticates credentials.

        If the credentials can be authenticated, return an object that provides
        IPrincipalInfo. If the plugin cannot authenticate the credentials,
        returns None.
        """
        if not IRPXNowCredentials.providedBy(credentials):
            return None

        token = credentials.token

        if token is None:
            return None

        info  = self._getRPXNowUserInfo(token)
        if not info:
            return None

        principalId = self.getPrincipalByRPXNowIdentifier(info['identifier'])
        if principalId is None:
            # Principal does not exist.
            principal = self._createPrincipal(info)
            name = INameChooser(self).chooseName('', principal)
            self[name] = principal
            principalId = self.getPrincipalByRPXNowIdentifier(info['identifier'])

        return self.principalInfo(self.prefix + principalId)

    def _createPrincipal(self, userInfo):
        principal = RPXNowPrincipal()
        principal.title = userInfo['name']['formatted']
        principal.identifier = userInfo['identifier']
        return principal

    def principalInfo(self, id):
        """Returns an IPrincipalInfo object for the specified principal id.

        If the plugin cannot find information for the id, returns None.
        """
        if id.startswith(self.prefix):
            internal = self.get(id[len(self.prefix):])
            if internal is not None:
                return RPXNowPrincipalInfo(id, internal)

    def getPrincipalByRPXNowIdentifier(self, identifier):
        """ return principal info by OpenID Identifier """
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
        info = RPXNowPrincipalInfo(self.prefix+id, internal)
        info.credentialsPlugin = None
        info.authenticatorPlugin = self
        principal = IFoundPrincipalFactory(info)(auth)
        principal.id = auth.prefix + self.prefix + id
        event.notify(PrincipalRemovingEvent(principal))

        # actual remove
        super(AuthenticatorPlugin, self).__delitem__(id)

        del self.__id_by_identifier[internal.identifier]


@component.adapter(IRPXNowUsersPlugin, IObjectRemovedEvent)
def pluginRemovedHandler(plugin, event):
    plugin = removeAllProxies(plugin)

    for id in plugin:
        del plugin[id]


authenticatorFactory = AuthenticatorPluginFactory(
    "principal.rpxnow", AuthenticatorPlugin, ((IRPXNowUsersPlugin, ''),),
    _(u'RPX Now plugin'),
    _(u'This plugin allow use rpxnow login '
      u'like google, yahoo, lifejournal and many others'))
