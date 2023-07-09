from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class NetworkAdminJSON(typing.TypedDict):
    kind: typing.Literal["NetworkAdmin"]


class CreateCatalogJSON(typing.TypedDict):
    kind: typing.Literal["CreateCatalog"]


class RemoveURLJSON(typing.TypedDict):
    kind: typing.Literal["RemoveURL"]


@dataclass
class NetworkAdmin:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "NetworkAdmin"

    @classmethod
    def to_json(cls) -> NetworkAdminJSON:
        return NetworkAdminJSON(
            kind="NetworkAdmin",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "NetworkAdmin": {},
        }


@dataclass
class CreateCatalog:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "CreateCatalog"

    @classmethod
    def to_json(cls) -> CreateCatalogJSON:
        return CreateCatalogJSON(
            kind="CreateCatalog",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "CreateCatalog": {},
        }


@dataclass
class RemoveURL:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "RemoveURL"

    @classmethod
    def to_json(cls) -> RemoveURLJSON:
        return RemoveURLJSON(
            kind="RemoveURL",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "RemoveURL": {},
        }


RoleKind = typing.Union[NetworkAdmin, CreateCatalog, RemoveURL]
RoleJSON = typing.Union[NetworkAdminJSON, CreateCatalogJSON, RemoveURLJSON]


def from_decoded(obj: dict) -> RoleKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "NetworkAdmin" in obj:
        return NetworkAdmin()
    if "CreateCatalog" in obj:
        return CreateCatalog()
    if "RemoveURL" in obj:
        return RemoveURL()
    raise ValueError("Invalid enum object")


def from_json(obj: RoleJSON) -> RoleKind:
    if obj["kind"] == "NetworkAdmin":
        return NetworkAdmin()
    if obj["kind"] == "CreateCatalog":
        return CreateCatalog()
    if obj["kind"] == "RemoveURL":
        return RemoveURL()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "NetworkAdmin" / borsh.CStruct(),
    "CreateCatalog" / borsh.CStruct(),
    "RemoveURL" / borsh.CStruct(),
)
