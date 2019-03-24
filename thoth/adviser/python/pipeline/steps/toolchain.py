#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2019 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""A step which reduces some of the toolchains to make sure they are always locked to a latest working version."""

import logging

from thoth.python import PackageVersion

from ..step import Step
from ..step_context import StepContext
from ..exceptions import CannotRemovePackage

_LOGGER = logging.getLogger(__name__)


class CutToolchain(Step):
    """Cut off packages which are toolchain.

    If packages considered in the "toolchain" group are present as direct dependencies, they are not removed.
    """

    _TOOLCHAIN_PACKAGE_NAMES = frozenset(("setuptools", "wheels", "pip"))

    def is_toolchain(self, package_version: PackageVersion):
        """Check if the given package is a toolchain package."""
        return package_version.name in self._TOOLCHAIN_PACKAGE_NAMES

    def run(self, step_context: StepContext):
        """Cut off packages from toolchain."""
        # reversed() to remove from the oldest ones so we keep new ones.
        # We cut off toolchain packages only in transitive dependency listing.
        for package_version in list(step_context.iter_transitive_dependencies()):
            package_tuple = package_version.to_tuple()
            if self.is_toolchain(package_version):
                with step_context.change(graceful=True) as step_change:
                    step_change.remove_package_tuple(package_tuple)
