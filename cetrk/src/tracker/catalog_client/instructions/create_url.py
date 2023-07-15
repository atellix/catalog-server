from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class CreateUrlArgs(typing.TypedDict):
    inp_url_expand_mode: int
    inp_url_hash: int
    inp_url_length: int
    inp_url: str


layout = borsh.CStruct(
    "inp_url_expand_mode" / borsh.U8,
    "inp_url_hash" / borsh.U128,
    "inp_url_length" / borsh.U32,
    "inp_url" / borsh.String,
)


class CreateUrlAccounts(typing.TypedDict):
    url_entry: Pubkey
    admin: Pubkey


def create_url(
    args: CreateUrlArgs,
    accounts: CreateUrlAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["url_entry"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"6\xc0\xb6\xa1\xfa\xa3\x8b{"
    encoded_args = layout.build(
        {
            "inp_url_expand_mode": args["inp_url_expand_mode"],
            "inp_url_hash": args["inp_url_hash"],
            "inp_url_length": args["inp_url_length"],
            "inp_url": args["inp_url"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
