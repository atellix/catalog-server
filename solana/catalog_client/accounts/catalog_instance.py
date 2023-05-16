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


class CatalogInstanceJSON(typing.TypedDict):
    catalog_id: int
    catalog_counter: int
    signer: str
    manager: str


@dataclass
class CatalogInstance:
    discriminator: typing.ClassVar = b"\xbe\xec\x10\x16\xf4'\x8f\xa3"
    layout: typing.ClassVar = borsh.CStruct(
        "catalog_id" / borsh.U64,
        "catalog_counter" / borsh.U64,
        "signer" / BorshPubkey,
        "manager" / BorshPubkey,
    )
    catalog_id: int
    catalog_counter: int
    signer: Pubkey
    manager: Pubkey

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["CatalogInstance"]:
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
    ) -> typing.List[typing.Optional["CatalogInstance"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["CatalogInstance"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "CatalogInstance":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = CatalogInstance.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            catalog_id=dec.catalog_id,
            catalog_counter=dec.catalog_counter,
            signer=dec.signer,
            manager=dec.manager,
        )

    def to_json(self) -> CatalogInstanceJSON:
        return {
            "catalog_id": self.catalog_id,
            "catalog_counter": self.catalog_counter,
            "signer": str(self.signer),
            "manager": str(self.manager),
        }

    @classmethod
    def from_json(cls, obj: CatalogInstanceJSON) -> "CatalogInstance":
        return cls(
            catalog_id=obj["catalog_id"],
            catalog_counter=obj["catalog_counter"],
            signer=Pubkey.from_string(obj["signer"]),
            manager=Pubkey.from_string(obj["manager"]),
        )
