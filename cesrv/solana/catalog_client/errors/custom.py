import typing
from anchorpy.error import ProgramError


class SigVerificationFailed(ProgramError):
    def __init__(self) -> None:
        super().__init__(6000, "Signature verification failed")

    code = 6000
    name = "SigVerificationFailed"
    msg = "Signature verification failed"


CustomError = typing.Union[SigVerificationFailed]
CUSTOM_ERROR_MAP: dict[int, CustomError] = {
    6000: SigVerificationFailed(),
}


def from_code(code: int) -> typing.Optional[CustomError]:
    maybe_err = CUSTOM_ERROR_MAP.get(code)
    if maybe_err is None:
        return None
    return maybe_err
