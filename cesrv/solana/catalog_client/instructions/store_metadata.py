from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class StoreMetadataArgs(typing.TypedDict):
    inp_program_name: str
    inp_developer_name: str
    inp_developer_url: str
    inp_source_url: str
    inp_verify_url: str


layout = borsh.CStruct(
    "inp_program_name" / borsh.String,
    "inp_developer_name" / borsh.String,
    "inp_developer_url" / borsh.String,
    "inp_source_url" / borsh.String,
    "inp_verify_url" / borsh.String,
)


class StoreMetadataAccounts(typing.TypedDict):
    program: Pubkey
    program_data: Pubkey
    program_admin: Pubkey
    program_info: Pubkey


def store_metadata(
    args: StoreMetadataArgs,
    accounts: StoreMetadataAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["program_data"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program_admin"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["program_info"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"x\x8b\xc1\xec\xa7%\nI"
    encoded_args = layout.build(
        {
            "inp_program_name": args["inp_program_name"],
            "inp_developer_name": args["inp_developer_name"],
            "inp_developer_url": args["inp_developer_url"],
            "inp_source_url": args["inp_source_url"],
            "inp_verify_url": args["inp_verify_url"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
