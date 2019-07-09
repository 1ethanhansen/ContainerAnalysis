import pytest

from utils.tests import travis_trial

def test_travis_1():
	assert(travis_trial() == True)
