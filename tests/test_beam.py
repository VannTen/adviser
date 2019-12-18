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

"""Test implementation of Beam search part in adviser's implementation."""

import pytest

from hypothesis import given
from hypothesis.strategies import integers
from thoth.adviser.beam import Beam
from thoth.adviser.state import State

from .base import AdviserTestCase


class TestBeam(AdviserTestCase):
    """Test beam implementation."""

    @given(integers(min_value=1))
    def test_initialization_positive(self, width: int) -> None:
        """Test initialization of beam."""
        beam = Beam(width=width)
        assert beam.width == width
        assert list(beam.iter_states()) == []

    @given(integers(max_value=0))
    def test_initialization_not_positive_error(self, width: int) -> None:
        """Test initialization of beam - passing negative or zero causes an exception being raised."""
        with pytest.raises(ValueError):
            Beam(width=width)

    def test_wipe(self) -> None:
        """Test wiping out beam states."""
        beam = Beam()

        state1 = State(score=1.0)
        beam.add_state(state1)

        state2 = State(score=0.0)
        beam.add_state(state2)

        assert list(beam.iter_states_sorted()) == [state1, state2]
        assert list(beam.iter_states()) == [state2, state1]

        assert beam.wipe() is None
        assert list(beam.iter_states_sorted()) == []
        assert list(beam.iter_states()) == []

        beam.add_state(state1)
        beam.add_state(state2)
        assert list(beam.iter_states_sorted()) == [state1, state2]
        assert list(beam.iter_states()) == [state2, state1]

    def test_add_state(self) -> None:
        """Test adding state to the beam - respect beam width."""
        beam = Beam(width=2)
        assert beam.width == 2

        state1 = State(score=1.0)
        beam.add_state(state1)
        assert beam.width == 2
        assert len(list(beam.iter_states())) == 1
        assert state1 in list(beam.iter_states())

        state2 = State(score=2.0)
        beam.add_state(state2)
        assert beam.width == 2
        assert len(list(beam.iter_states())) == 2
        assert state2 in list(beam.iter_states())

        state3 = State(score=3.0)
        beam.add_state(state3)
        assert beam.width == 2
        assert len(list(beam.iter_states())) == 2
        assert state3 in list(beam.iter_states())
        assert state2 in list(beam.iter_states())
        assert state1 not in list(beam.iter_states())

        state0 = State(score=0.0)
        beam.add_state(state0)
        assert beam.width == 2
        assert len(list(beam.iter_states())) == 2
        assert state3 in list(beam.iter_states())
        assert state2 in list(beam.iter_states())
        assert state1 not in list(beam.iter_states())
        assert state0 not in list(beam.iter_states())

    def test_iter_states_sorted(self) -> None:
        """Test asking for states returns a sorted list of states."""
        beam = Beam(width=4)
        assert beam.width == 4

        state1 = State(score=1.0)
        beam.add_state(state1)
        state3 = State(score=3.0)
        beam.add_state(state3)
        state0 = State(score=0.0)
        beam.add_state(state0)
        state2 = State(score=2.0)
        beam.add_state(state2)

        assert list(beam.iter_states_sorted()) == [state3, state2, state1, state0]

    def test_top(self) -> None:
        """Test top element in beam."""
        beam = Beam(width=2)
        assert beam.width == 2

        state1 = State(score=1.0)
        beam.add_state(state1)
        assert beam.top() is state1

        state2 = State(score=2.0)
        beam.add_state(state2)
        assert beam.top() is state2

        state3 = State(score=0.5)
        beam.add_state(state3)
        assert beam.top() is state2

    def test_add_state_order_multi(self) -> None:
        """Test adding states to beam and order during addition when score is same."""
        beam = Beam(width=2)

        state01 = State(score=0.0, iteration=0, iteration_states_added=0)
        state01.add_justification([{"state": "01"}])
        beam.add_state(state01)

        state02 = State(score=0.0, iteration=0, iteration_states_added=1)
        state02.add_justification([{"state": "02"}])
        beam.add_state(state02)

        state03 = State(score=0.0, iteration=1, iteration_states_added=0)
        state03.add_justification([{"state": "03"}])
        beam.add_state(state03)

        state04 = State(score=0.0, iteration=1, iteration_states_added=1)
        state04.add_justification([{"state": "04"}])
        beam.add_state(state04)

        assert list(beam.iter_states_sorted()) == [state03, state04]
        assert list(beam.iter_states_sorted(reverse=True)) == [state03, state04]
        assert list(beam.iter_states_sorted(reverse=False)) == [state04, state03]

    def test_add_state_order_single(self) -> None:
        """Test adding states to beam and order during addition when score is same - iteration is relevant."""
        beam = Beam(width=1)

        state01 = State(
            score=0.0,
            latest_version_offset=0,
            iteration=1,
            iteration_states_added=0,
        )
        state01.add_justification([{"state": "01"}])
        beam.add_state(state01)

        state02 = State(
            score=0.0,
            latest_version_offset=0,
            iteration=0,
            iteration_states_added=0,
        )
        state02.add_justification([{"state": "02"}])
        beam.add_state(state02)

        assert list(beam.iter_states()) == [state01]
        assert list(beam.iter_states_sorted(reverse=True)) == [state01]
        assert list(beam.iter_states_sorted(reverse=False)) == [state01]

    def test_new_iteration(self) -> None:
        """Test marking a new iteration in a resolution round."""
        beam = Beam(width=2)

        assert list(beam.iter_states()) == []
        assert list(beam.iter_new_added_states()) == []

        state01 = State(score=0.0)
        beam.add_state(state01)

        assert list(beam.iter_states()) == [state01]
        assert list(beam.iter_new_added_states()) == [state01]

        beam.new_iteration()

        assert list(beam.iter_states()) == [state01]
        assert list(beam.iter_new_added_states()) == []

        state02 = State(score=0.1)
        beam.add_state(state02)

        assert state01 in beam.iter_states()
        assert state02 in beam.iter_states()
        assert list(beam.iter_new_added_states()) == [state02]

        beam.new_iteration()

        state03 = State(score=0.2)
        beam.add_state(state03)

        state04 = State(score=0.3)
        beam.add_state(state04)

        state05 = State(score=0.4)
        beam.add_state(state05)

        assert beam.size == 2
        assert state04 in beam.iter_states()
        assert state05 in beam.iter_states()

        new_added = list(beam.iter_new_added_states())
        assert len(new_added) == 2
        assert state04 in new_added
        assert state05 in new_added

        assert list(beam.iter_new_added_states_sorted()) == [state05, state04]
        assert list(beam.iter_new_added_states_sorted(reverse=True)) == [state05, state04]
        assert list(beam.iter_new_added_states_sorted(reverse=False)) == [state04, state05]

        beam.new_iteration()

        state06 = State(score=1.0)
        beam.add_state(state06)

        state07 = State(score=1.0)
        beam.add_state(state07)

        assert list(beam.iter_new_added_states_sorted()) == [state06, state07]
        assert list(beam.iter_new_added_states_sorted(reverse=True)) == [state06, state07]
        assert list(beam.iter_new_added_states_sorted(reverse=False)) == [state06, state07]

    def test_remove(self) -> None:
        """Test removal of a state from beam."""
        beam = Beam(width=2)

        state1 = State(score=0.0)
        beam.add_state(state1)
        beam.remove(state1)

        state2 = State(score=1.0)
        beam.add_state(state2)
        beam.remove(state2)

        state3 = State(score=2.0)
        beam.add_state(state3)
        beam.remove(state3)

        assert beam.size == 0

        beam.add_state(state1)
        beam.add_state(state2)
        beam.add_state(state3)

        assert state1 not in beam.iter_states()
        assert state2 in beam.iter_states()
        assert state3 in beam.iter_states()

        with pytest.raises(KeyError):
            beam.remove(state1)

        beam.remove(state2)

        assert state2 not in beam.iter_states()
        assert state3 in beam.iter_states()
        assert beam.size == 1

        beam.remove(state3)

        assert beam.size == 0
        assert state3 not in beam.iter_states()
