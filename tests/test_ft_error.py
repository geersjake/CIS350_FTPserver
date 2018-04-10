# pylint: disable = missing-docstring, missing-return-doc, missing-return-type-doc
# pylint: disable = invalid-name
# pylint: disable = no-self-use
# pylint: disable = protected-access

import pytest
from ft_conn.ft_error import UnexpectedValueError, BrokenSocketError

class TestFTErrors:
    def test_uve(self):
        with pytest.raises(UnexpectedValueError) as e:
            raise UnexpectedValueError('Expected', 'Got')

        assert e.value.__repr__() == "UnexpectedValueError('Expected', 'Got')"
        assert e.value.__str__() == "Expected 'Expected', but got 'Got'"

    def test_bse(self):
        with pytest.raises(BrokenSocketError) as e:
            raise BrokenSocketError()

        assert e.value.__str__() == "Socket broken unexpectedly"
