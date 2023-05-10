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


class ProgramMetadataJSON(typing.TypedDict):
    semvar_major: int
    semvar_minor: int
    semvar_patch: int
    program: str
    program_name: str
    developer_name: str
    developer_url: str
    source_url: str
    verify_url: str


@dataclass
class ProgramMetadata:
    discriminator: typing.ClassVar = b"#k!\x16\xf6\x9c\xd2\xc3"
    layout: typing.ClassVar = borsh.CStruct(
        "semvar_major" / borsh.U32,
        "semvar_minor" / borsh.U32,
        "semvar_patch" / borsh.U32,
        "program" / BorshPubkey,
        "program_name" / borsh.String,
        "developer_name" / borsh.String,
        "developer_url" / borsh.String,
        "source_url" / borsh.String,
        "verify_url" / borsh.String,
    )
    semvar_major: int
    semvar_minor: int
    semvar_patch: int
    program: Pubkey
    program_name: str
    developer_name: str
    developer_url: str
    source_url: str
    verify_url: str

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["ProgramMetadata"]:
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
    ) -> typing.List[typing.Optional["ProgramMetadata"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["ProgramMetadata"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "ProgramMetadata":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = ProgramMetadata.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            semvar_major=dec.semvar_major,
            semvar_minor=dec.semvar_minor,
            semvar_patch=dec.semvar_patch,
            program=dec.program,
            program_name=dec.program_name,
            developer_name=dec.developer_name,
            developer_url=dec.developer_url,
            source_url=dec.source_url,
            verify_url=dec.verify_url,
        )

    def to_json(self) -> ProgramMetadataJSON:
        return {
            "semvar_major": self.semvar_major,
            "semvar_minor": self.semvar_minor,
            "semvar_patch": self.semvar_patch,
            "program": str(self.program),
            "program_name": self.program_name,
            "developer_name": self.developer_name,
            "developer_url": self.developer_url,
            "source_url": self.source_url,
            "verify_url": self.verify_url,
        }

    @classmethod
    def from_json(cls, obj: ProgramMetadataJSON) -> "ProgramMetadata":
        return cls(
            semvar_major=obj["semvar_major"],
            semvar_minor=obj["semvar_minor"],
            semvar_patch=obj["semvar_patch"],
            program=Pubkey.from_string(obj["program"]),
            program_name=obj["program_name"],
            developer_name=obj["developer_name"],
            developer_url=obj["developer_url"],
            source_url=obj["source_url"],
            verify_url=obj["verify_url"],
        )
