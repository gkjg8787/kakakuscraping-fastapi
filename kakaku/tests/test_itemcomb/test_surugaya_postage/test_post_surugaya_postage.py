import requests
from requests import exceptions
import socket

import pytest

from itemcomb.surugaya_postage import post_surugaya_postage as psp


def test_getRawShippingFee_timeout(mocker):
    mocker.patch("requests.post", side_effect=exceptions.Timeout())
    a = psp.getRawShippingFee(tenpo_cd=0)
    assert a is None


def test_getRawShippingFee_connectionerror_gaierror(mocker):
    mocker.patch("socket._socket.getaddrinfo", side_effect=socket.gaierror)
    a = psp.getRawShippingFee(tenpo_cd=0)
    assert a is None
