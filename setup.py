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
"""Setup for zojax.principal.rpxnow package

$Id$
"""
import sys, os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version='0'


setup(name = 'zojax.principal.rpxnow',
      version = version,
      description = "RpxNow authentication module for zojax.",
      long_description = (
          'Detailed Documentation\n' +
          '======================\n'
          + '\n\n' +
          read('CHANGES.txt')
          ),
      classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Framework :: Zope3'],
      keywords = 'Zope3, RpxNow',
      author = 'Anatoly Bubenkov',
      author_email = 'bubenkoff@gmail.com',
      url = '',
      license = 'ZPL 2.1',
      include_package_data = True,
      zip_safe = False,
      packages = find_packages('src'),
      package_dir = {'':'src'},
      namespace_packages = ['zojax', 'zojax.principal'],
      install_requires = ['setuptools',
                          'zc.blist',
                          'zope.session',
                          'zope.cachedescriptors',
                          'zope.app.container',
                          'zojax.authentication',
                          'zojax.statusmessage',
                          'zojax.principal.registration',
                          ],
      extras_require = dict(test = ['zope.app.testing',
                                    ])
      )
