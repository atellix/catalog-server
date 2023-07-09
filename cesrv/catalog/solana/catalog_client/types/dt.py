from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class UserRBACMapJSON(typing.TypedDict):
    kind: typing.Literal["UserRBACMap"]


class UserRBACJSON(typing.TypedDict):
    kind: typing.Literal["UserRBAC"]


@dataclass
class UserRBACMap:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "UserRBACMap"

    @classmethod
    def to_json(cls) -> UserRBACMapJSON:
        return UserRBACMapJSON(
            kind="UserRBACMap",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "UserRBACMap": {},
        }


@dataclass
class UserRBAC:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "UserRBAC"

    @classmethod
    def to_json(cls) -> UserRBACJSON:
        return UserRBACJSON(
            kind="UserRBAC",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "UserRBAC": {},
        }


DTKind = typing.Union[UserRBACMap, UserRBAC]
DTJSON = typing.Union[UserRBACMapJSON, UserRBACJSON]


def from_decoded(obj: dict) -> DTKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "UserRBACMap" in obj:
        return UserRBACMap()
    if "UserRBAC" in obj:
        return UserRBAC()
    raise ValueError("Invalid enum object")


def from_json(obj: DTJSON) -> DTKind:
    if obj["kind"] == "UserRBACMap":
        return UserRBACMap()
    if obj["kind"] == "UserRBAC":
        return UserRBAC()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen("UserRBACMap" / borsh.CStruct(), "UserRBAC" / borsh.CStruct())
