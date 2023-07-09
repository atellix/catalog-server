from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class RemoveListingAccounts(typing.TypedDict):
    catalog: Pubkey
    listing: Pubkey
    fee_recipient: Pubkey
    auth_user: Pubkey


def remove_listing(
    accounts: RemoveListingAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["catalog"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["listing"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["fee_recipient"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["auth_user"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"J\x05\xec\x07\x02h\x8br"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
