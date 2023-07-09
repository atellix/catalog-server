from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class CreateCatalogArgs(typing.TypedDict):
    inp_catalog: int


layout = borsh.CStruct("inp_catalog" / borsh.U64)


class CreateCatalogAccounts(typing.TypedDict):
    root_data: Pubkey
    auth_data: Pubkey
    auth_user: Pubkey
    catalog: Pubkey
    catalog_signer: Pubkey
    catalog_manager: Pubkey
    fee_payer: Pubkey


def create_catalog(
    args: CreateCatalogArgs,
    accounts: CreateCatalogAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["root_data"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["auth_data"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["auth_user"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["catalog"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["catalog_signer"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["catalog_manager"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["fee_payer"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x06\xe4\xd9b8iN\xb9"
    encoded_args = layout.build(
        {
            "inp_catalog": args["inp_catalog"],
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
