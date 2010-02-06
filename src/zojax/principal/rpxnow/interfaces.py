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
""" zojax.principal.rpxnow interfaces

$Id$
"""
from zope import interface, schema
from zope.i18nmessageid.message import MessageFactory
from zope.app.authentication.interfaces import IPrincipalInfo
from zope.app.authentication.interfaces import IAuthenticatorPlugin


_ = MessageFactory("zojax.principal.rpxnow")
SESSION_KEY = 'zojax.principal.rpxnow'


class IRPXNowAuthenticationProduct(interface.Interface):
    """ product """

    apiKey = schema.TextLine(title=_(u"API key"),
                                  required=True,)

    rpcURL = schema.TextLine(title=_(u"RPC url"),
                                default=u'https://rpxnow.com/api/v2',
                                required=True,)

    cookieNames = interface.Attribute(u"Cookie name")


class IRPXNowPrincipal(interface.Interface):
    """ rpxnow principal """

    title = schema.TextLine(
        title = _('Title'),
        required = True)

    identifier = interface.Attribute('OpenID Identifier')


class IRPXNowPrincipalInfo(IPrincipalInfo):
    """ principal info """

    internalId = interface.Attribute('OpenID Identifier')


class IRPXNowPrincipalMarker(interface.Interface):
    """ openId principal marker """


class IRPXNowAuthenticator(interface.Interface):

    def getPrincipalByRPXNowIdentifier(identifier):
        """ Get principal id by her OpenID identifier. Return None if
        principal with given identifier does not exist. """


class IRPXNowCredentials(interface.Interface):
    """ open id credentials info """

    token = interface.Attribute(u"token")


class IRPXNowUsersPlugin(IRPXNowAuthenticator, IAuthenticatorPlugin):
    """A container that contains rpxnow principals."""

    title = schema.TextLine(
        title = _('Title'),
        required = False)

    prefix = schema.TextLine(
        title=_("Prefix"),
        description=_("Prefix to be added to all principal ids to assure "
                      "that all ids are unique within the authentication service"),
        missing_value=u"",
        default=u'',
        readonly=True)

    def getPrincipalByLogin(login):
        """ return principal info by login """
