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


class CatalogEntryJSON(typing.TypedDict):
    uuid: int
    catalog: int
    category: int
    filter_by: list[int]
    attributes: int
    latitude: int
    longitude: int
    update_ts: int
    update_count: int
    owner: str
    listing_idx: int
    listing_url: str
    label_url: str
    detail_url: str


@dataclass
class CatalogEntry:
    discriminator: typing.ClassVar = b"'\xea\xf9^(2\xf4I"
    layout: typing.ClassVar = borsh.CStruct(
        "uuid" / borsh.U128,
        "catalog" / borsh.U64,
        "category" / borsh.U128,
        "filter_by" / borsh.U128[3],
        "attributes" / borsh.U8,
        "latitude" / borsh.I32,
        "longitude" / borsh.I32,
        "update_ts" / borsh.I64,
        "update_count" / borsh.U64,
        "owner" / BorshPubkey,
        "listing_idx" / borsh.U64,
        "listing_url" / BorshPubkey,
        "label_url" / BorshPubkey,
        "detail_url" / BorshPubkey,
    )
    uuid: int
    catalog: int
    category: int
    filter_by: list[int]
    attributes: int
    latitude: int
    longitude: int
    update_ts: int
    update_count: int
    owner: Pubkey
    listing_idx: int
    listing_url: Pubkey
    label_url: Pubkey
    detail_url: Pubkey

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["CatalogEntry"]:
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
    ) -> typing.List[typing.Optional["CatalogEntry"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["CatalogEntry"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "CatalogEntry":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = CatalogEntry.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            uuid=dec.uuid,
            catalog=dec.catalog,
            category=dec.category,
            filter_by=dec.filter_by,
            attributes=dec.attributes,
            latitude=dec.latitude,
            longitude=dec.longitude,
            update_ts=dec.update_ts,
            update_count=dec.update_count,
            owner=dec.owner,
            listing_idx=dec.listing_idx,
            listing_url=dec.listing_url,
            label_url=dec.label_url,
            detail_url=dec.detail_url,
        )

    def to_json(self) -> CatalogEntryJSON:
        return {
            "uuid": self.uuid,
            "catalog": self.catalog,
            "category": self.category,
            "filter_by": self.filter_by,
            "attributes": self.attributes,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "update_ts": self.update_ts,
            "update_count": self.update_count,
            "owner": str(self.owner),
            "listing_idx": self.listing_idx,
            "listing_url": str(self.listing_url),
            "label_url": str(self.label_url),
            "detail_url": str(self.detail_url),
        }

    @classmethod
    def from_json(cls, obj: CatalogEntryJSON) -> "CatalogEntry":
        return cls(
            uuid=obj["uuid"],
            catalog=obj["catalog"],
            category=obj["category"],
            filter_by=obj["filter_by"],
            attributes=obj["attributes"],
            latitude=obj["latitude"],
            longitude=obj["longitude"],
            update_ts=obj["update_ts"],
            update_count=obj["update_count"],
            owner=Pubkey.from_string(obj["owner"]),
            listing_idx=obj["listing_idx"],
            listing_url=Pubkey.from_string(obj["listing_url"]),
            label_url=Pubkey.from_string(obj["label_url"]),
            detail_url=Pubkey.from_string(obj["detail_url"]),
        )
