from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from spl.token.constants import TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class CreateListingArgs(typing.TypedDict):
    inp_uuid: int


layout = borsh.CStruct("inp_uuid" / borsh.U128)


class CreateListingAccounts(typing.TypedDict):
    catalog: Pubkey
    listing: Pubkey
    owner: Pubkey
    ix_sysvar: Pubkey
    fee_payer: Pubkey
    fee_source: Pubkey
    fee_account: Pubkey


def create_listing(
    args: CreateListingArgs,
    accounts: CreateListingAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["catalog"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["listing"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["ix_sysvar"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["fee_payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["fee_source"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["fee_account"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x12\xa8-\x18\xbf\x1fu6"
    encoded_args = layout.build(
        {
            "inp_uuid": args["inp_uuid"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
