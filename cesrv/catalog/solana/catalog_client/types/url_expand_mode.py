from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class NoneJSON(typing.TypedDict):
    kind: typing.Literal["None"]


class AppendUUIDJSON(typing.TypedDict):
    kind: typing.Literal["AppendUUID"]


class UTF8UriEncodedJSON(typing.TypedDict):
    kind: typing.Literal["UTF8UriEncoded"]


@dataclass
class None_:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "None"

    @classmethod
    def to_json(cls) -> NoneJSON:
        return NoneJSON(
            kind="None",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "None": {},
        }


@dataclass
class AppendUUID:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "AppendUUID"

    @classmethod
    def to_json(cls) -> AppendUUIDJSON:
        return AppendUUIDJSON(
            kind="AppendUUID",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "AppendUUID": {},
        }


@dataclass
class UTF8UriEncoded:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "UTF8UriEncoded"

    @classmethod
    def to_json(cls) -> UTF8UriEncodedJSON:
        return UTF8UriEncodedJSON(
            kind="UTF8UriEncoded",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "UTF8UriEncoded": {},
        }


URLExpandModeKind = typing.Union[None_, AppendUUID, UTF8UriEncoded]
URLExpandModeJSON = typing.Union[NoneJSON, AppendUUIDJSON, UTF8UriEncodedJSON]


def from_decoded(obj: dict) -> URLExpandModeKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "None" in obj:
        return None_()
    if "AppendUUID" in obj:
        return AppendUUID()
    if "UTF8UriEncoded" in obj:
        return UTF8UriEncoded()
    raise ValueError("Invalid enum object")


def from_json(obj: URLExpandModeJSON) -> URLExpandModeKind:
    if obj["kind"] == "None":
        return None_()
    if obj["kind"] == "AppendUUID":
        return AppendUUID()
    if obj["kind"] == "UTF8UriEncoded":
        return UTF8UriEncoded()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "None" / borsh.CStruct(),
    "AppendUUID" / borsh.CStruct(),
    "UTF8UriEncoded" / borsh.CStruct(),
)
