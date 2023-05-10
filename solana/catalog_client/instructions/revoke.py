from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class RevokeArgs(typing.TypedDict):
    inp_root_nonce: int
    inp_role: int


layout = borsh.CStruct("inp_root_nonce" / borsh.U8, "inp_role" / borsh.U32)


class RevokeAccounts(typing.TypedDict):
    root_data: Pubkey
    auth_data: Pubkey
    program: Pubkey
    program_data: Pubkey
    program_admin: Pubkey
    rbac_user: Pubkey


def revoke(
    args: RevokeArgs,
    accounts: RevokeAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["root_data"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["auth_data"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["program_data"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program_admin"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["rbac_user"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b'\xaa\x17\x1f"\x85\xad]\xf2'
    encoded_args = layout.build(
        {
            "inp_root_nonce": args["inp_root_nonce"],
            "inp_role": args["inp_role"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
