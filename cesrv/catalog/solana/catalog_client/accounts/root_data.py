import typing
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from anchorpy.borsh_extension import BorshPubkey
from ..program_id import PROGRAM_ID


class RootDataJSON(typing.TypedDict):
    catalog_count: int
    root_authority: str


@dataclass
class RootData:
    discriminator: typing.ClassVar = b"n\xbf_UI~Z\x8c"
    layout: typing.ClassVar = borsh.CStruct(
        "catalog_count" / borsh.U64, "root_authority" / BorshPubkey
    )
    catalog_count: int
    root_authority: Pubkey

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["RootData"]:
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
    ) -> typing.List[typing.Optional["RootData"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["RootData"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "RootData":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = RootData.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            catalog_count=dec.catalog_count,
            root_authority=dec.root_authority,
        )

    def to_json(self) -> RootDataJSON:
        return {
            "catalog_count": self.catalog_count,
            "root_authority": str(self.root_authority),
        }

    @classmethod
    def from_json(cls, obj: RootDataJSON) -> "RootData":
        return cls(
            catalog_count=obj["catalog_count"],
            root_authority=Pubkey.from_string(obj["root_authority"]),
        )
