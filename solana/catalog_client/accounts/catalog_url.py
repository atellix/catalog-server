import typing
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from ..program_id import PROGRAM_ID


class CatalogUrlJSON(typing.TypedDict):
    url_expand_mode: int
    url: str


@dataclass
class CatalogUrl:
    discriminator: typing.ClassVar = b"\n*\xe3\xb4\x01\x11^\x18"
    layout: typing.ClassVar = borsh.CStruct(
        "url_expand_mode" / borsh.U8, "url" / borsh.String
    )
    url_expand_mode: int
    url: str

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["CatalogUrl"]:
        resp = await conn.get_account_info(address, commitment=commitment)
        info = resp.value
        if info is None:
            return None
        if info.owner != program_id:
            raise ValueError("Account does not belong to this program")
        bytes_data = info.data
        return cls.decode(bytes_data)

    @classmethod
    async def fetch_multiple(
        cls,
        conn: AsyncClient,
        addresses: list[Pubkey],
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.List[typing.Optional["CatalogUrl"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["CatalogUrl"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "CatalogUrl":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = CatalogUrl.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            url_expand_mode=dec.url_expand_mode,
            url=dec.url,
        )

    def to_json(self) -> CatalogUrlJSON:
        return {
            "url_expand_mode": self.url_expand_mode,
            "url": self.url,
        }

    @classmethod
    def from_json(cls, obj: CatalogUrlJSON) -> "CatalogUrl":
        return cls(
            url_expand_mode=obj["url_expand_mode"],
            url=obj["url"],
        )
