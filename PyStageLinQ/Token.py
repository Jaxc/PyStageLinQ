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
        randomized_bytes = bytearray(randbytes(self.TOKENLENGTH))

        # check if first bit is set and set bit to 0 if so.
        if randomized_bytes[0] >= 128:
            randomized_bytes[0] = randomized_bytes[0] - 128

        self.token = int.from_bytes(randomized_bytes, byteorder='big')

    def get_token(self):
        return self.token

    def set_token(self, token) -> int:
        if type(token) == int:
            if self.validate_token(token) == PyStageLinQError.STAGELINQOK:
                self.token = token
            else:
                raise Exception("Token could not be Validated")
        else:
            raise Exception("Token is not of type int")

    def validate_token(self, token) -> int:
        ret = PyStageLinQError.INVALIDTOKEN
        # The token is validated by converting it to a 16 byte array and then back to an int. If the value is the same
        # the token is considered valid
        token_bytes = token.to_bytes(StageLinQToken.TOKENLENGTH, byteorder='big')
        if token == int.from_bytes(token_bytes, byteorder='big'):
            ret = PyStageLinQError.STAGELINQOK

        return ret
