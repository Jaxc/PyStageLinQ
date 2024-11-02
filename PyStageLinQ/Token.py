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
        self.token = 0

    def generate_token(self):
        """
        A function to generate the token.

        NOTE:
        The tokens MSB cannot have the 0x80 bit set, this will cause the device to not send services

        :return: No return value
        """
        randomized_bytes = self._get_randomized_bytes(self.TOKENLENGTH)

        # The following checks are to solve issues with invalid token values I've found when testing. The actual token
        # structure is currently unknown, so a random value is generated as this seems to be what's going on from the
        # devices I've tested against.
        invalid_token_bit_mask = ~(0x1 << 127 | 0xC << 60)

        self.token = (
            int.from_bytes(randomized_bytes, byteorder="big") & invalid_token_bit_mask
        )

    @staticmethod
    def _get_randomized_bytes(length: int) -> bytes:
        randomized_bytes = bytearray(randbytes(length))
        return randomized_bytes

    def get_token(self) -> int:
        return self.token

    def set_token(self, token: int) -> None:
        if type(token) == int:
            if self.validate_token(token) == PyStageLinQError.STAGELINQOK:
                self.token = token
            else:
                # Token could not be Validated
                raise PyStageLinQError.INVALIDTOKEN
        else:
            # Token is not of type int
            raise PyStageLinQError.INVALIDTOKENTYPE

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
