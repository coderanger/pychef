# Copyright (C) 2012 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of versiontools.
#
# versiontools is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation
#
# versiontools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with versiontools.  If not, see <http://www.gnu.org/licenses/>.

"""
versiontools.versiontools_support
=================================

A small standalone module that allows any package to use versiontools.

Typically you should copy this file verbatim into your source distribution.

Historically versiontools was depending on a exotic feature of setuptools to
work. Setuptools has so-called setup-time dependencies, that is modules that
need to be downloaded and imported/interrogated for setup.py to run
successfully. Versiontools supports this by installing a handler for the
'version' keyword of the setup() function.

This approach was always a little annoying as this setuptools feature is rather
odd and very few other packages made any use of it. In the future the standard
tools for python packaging (especially in python3 world) this feature may be
removed or have equivalent thus rendering versiontools completely broken.

Currently the biggest practical issue is the apparent inability to prevent
setuptools from downloading packages designated as setup_requires. This is
discussed in this pip issue: https://github.com/pypa/pip/issues/410

To counter this issue I've redesigned versiontools to be a little smarter. The
old mode stays as-is for compatibility. The new mode works differently, without
the need for using setup_requires in your setup() call. Instead it requires
each package that uses versiontools to ship a verbatim copy of this module and
to import it in their setup.py script. This module helps setuptools find
package version in the standard PKG-INFO file that is created for all source
distributions. Remember that you only need this mode when you don't want to add
a dependency on versiontools. This will still allow you to use versiontools (in
a limited way) in your setup.py file.

Technically this module defines an improved version of one of
distutils.dist.DistributionMetadata class and monkey-patches distutils to use
it. To retain backward compatibility the new feature is only active when a
special version string is passed to the setup() call.
"""

__version__ = (1, 0, 0, "final", 0)

import distutils.dist
import distutils.errors


class VersiontoolsEnchancedDistributionMetadata(distutils.dist.DistributionMetadata):
    """
    A subclass of distutils.dist.DistributionMetadata that uses versiontools

    Typically you would not instantiate this class directly. It is constructed
    by distutils.dist.Distribution.__init__() method. Since there is no other
    way to do it, this module monkey-patches distutils to override the original
    version of DistributionMetadata
    """

    # Reference to the original class. This is only required because distutils
    # was created before the introduction of new-style classes to python.
    __base = distutils.dist.DistributionMetadata

    def get_version(self): 
        """
        Get distribution version.

        This method is enhanced compared to original distutils implementation.
        If the version string is set to a special value then instead of using
        the actual value the real version is obtained by querying versiontools.

        If versiontools package is not installed then the version is obtained
        from the standard section of the ``PKG-INFO`` file. This file is
        automatically created by any source distribution. This method is less
        useful as it cannot take advantage of version control information that
        is automatically loaded by versiontools. It has the advantage of not
        requiring versiontools installation and that it does not depend on
        ``setup_requires`` feature of ``setuptools``.
        """
        if (self.name is not None and self.version is not None
            and self.version.startswith(":versiontools:")):
            return (self.__get_live_version() or self.__get_frozen_version()
                    or self.__fail_to_get_any_version())
        else:
            return self.__base.get_version(self)

    def __get_live_version(self):
        """
        Get a live version string using versiontools
        """
        try:
            import versiontools
        except ImportError:
            return None
        else:
            return str(versiontools.Version.from_expression(self.name))

    def __get_frozen_version(self):
        """
        Get a fixed version string using an existing PKG-INFO file
        """
        try:
            return self.__base("PKG-INFO").version
        except IOError:
            return None

    def __fail_to_get_any_version(self):
        """
        Raise an informative exception
        """
        raise SystemExit(
"""This package requires versiontools for development or testing.

See http://versiontools.readthedocs.org/ for more information about
what versiontools is and why it is useful.

To install versiontools now please run:
    $ pip install versiontools

Note: versiontools works best when you have additional modules for
integrating with your preferred version control system. Refer to
the documentation for a full list of required modules.""")


# If DistributionMetadata is not a subclass of
# VersiontoolsEnhancedDistributionMetadata then monkey patch it. This should
# prevent a (odd) case of multiple imports of this module.
if not issubclass(
    distutils.dist.DistributionMetadata,
    VersiontoolsEnchancedDistributionMetadata):
    distutils.dist.DistributionMetadata = VersiontoolsEnchancedDistributionMetadata
