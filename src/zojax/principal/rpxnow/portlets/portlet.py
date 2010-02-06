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
import random, sys

from zope import component
from zope.app.component.hooks import getSite
from zope.traversing.browser import absoluteURL

from zojax.portlets.htmlsource.portlet import HTMLSourcePortlet
from zojax.resourcepackage import library

from zojax.principal.rpxnow.interfaces import IRPXNowAuthenticationProduct


script = r"""
<script type="text/javascript">
  var rpxJsHost = (("https:" == document.location.protocol) ? "https://" : "http://static.");
  document.write(unescape("%3Cscript src='" + rpxJsHost +
"rpxnow.com/js/lib/rpx.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
  RPXNOW.overlay = true;
  RPXNOW.language_preference = 'en';
</script>
"""

class RPXNow(HTMLSourcePortlet):

    def update(self):
        super(RPXNow, self).update()
        product = component.getUtility(IRPXNowAuthenticationProduct)
        source = script % dict(successURL='%s/login-success.html'%absoluteURL(getSite(), self.request))
        if source not in library.includes.sources:
            library.includeInplaceSource(source)
