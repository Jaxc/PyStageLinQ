"""
(c) 2022 Jaxcie
This code is licensed under MIT license (see LICENSE for details)
"""

from random import randbytes
from .ErrorCodes import PyStageLinQError


class StageLinQToken:
    TOKENLENGTH = 16
    token: int

    def __init__(self):


    def generate_token(self):
        """
        A function to generate the token.

        NOTE:
        The tokens MSB cannot have the 0x80 bit set, this will cause the device to not send services

        :return: No return value
        """
        randomized_bytes = self._get_randomized_bytes(self.TOKENLENGTH)

        # check if first bit is set and set bit to 0 if so.
        if randomized_bytes[0] >= 128:
            randomized_bytes[0] = randomized_bytes[0] - 128

        self.token = int.from_bytes(randomized_bytes, byteorder="big")

    @staticmethod
    def _get_randomized_bytes(length: int) -> bytes:
        randomized_bytes = bytearray(randbytes(length))
        return randomized_bytes

    def get_token(self) -> int:
        return self.token

    def set_token(self, token: int) -> PyStageLinQError:
        if type(token) == int:
            if self.validate_token(token) == PyStageLinQError.STAGELINQOK:
                self.token = token
                ret = PyStageLinQError.STAGELINQOK
            else:
                # Token could not be Validated
                ret = PyStageLinQError.INVALIDTOKEN
        else:
            # Token is not of type int
            ret = PyStageLinQError.INVALIDTOKENTYPE

        return ret

    @staticmethod
    def validate_token(token: int) -> PyStageLinQError:
        # The token is validated by converting it to a 16 byte array and then back to an int. If the value is the same
        # the token is considered valid
        if token.bit_length() <= StageLinQToken.TOKENLENGTH * 8:
            if token > 0:
                ret = PyStageLinQError.STAGELINQOK

            else:
                ret = PyStageLinQError.INVALIDTOKEN

        else:
            ret = PyStageLinQError.INVALIDTOKENLENGTH

        return ret
