# SPDX-FileCopyrightText: © 2025 Evotis S.A.S.
# SPDX-License-Identifier: Apache-2.0


class RootException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class KajsonException(RootException):
    pass


class ClassRegistryInheritanceError(KajsonException):
    pass


class ClassRegistryNotFoundError(KajsonException):
    pass


class KajsonDecoderError(KajsonException):
    pass


class UnijsonEncoderError(KajsonException):
    pass
