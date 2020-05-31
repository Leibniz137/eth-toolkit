import json
from pathlib import Path

from fabric import task
from hexbytes import HexBytes
from web3 import (
    Web3,
)
from web3.gas_strategies.time_based import medium_gas_price_strategy
from web3.middleware import geth_poa_middleware


# KOVAN_URL = 'https://kovan.infura.io/v3/029890c5690243edbcb9fc201eb85164'
# KOVAN_URL = 'https://kovan.infura.io/v3/11ca986655fb407ca5d56b996b693632'
# PROVIDER = Web3.HTTPProvider(KOVAN_URL)
DAPPNODE_URL = 'http://geth.dappnode:8545'
RINKEBY_CHAIN_ID = 4
# INFURA_URL = 'https://mainnet.infura.io/v3/11ca986655fb407ca5d56b996b693632'
PROVIDER = Web3.HTTPProvider(DAPPNODE_URL)
W3 = Web3(PROVIDER)


class HexJsonEncoder(json.JSONEncoder):
    """
    https://github.com/ethereum/web3.py/issues/782#issuecomment-383464754
    """
    def default(self, obj):
        if isinstance(obj, HexBytes):
            return obj.hex()
        return super().default(obj)



# select *
# from `bigquery-public-data.crypto_ethereum.INFORMATION_SCHEMA.TABLES`;


@task
def rinkeby_send(c, amount, recipient):
    url = 'https://rinkeby.infura.io/v3/f283308c432944ae902218cd69bc2229'
    provider = Web3.HTTPProvider(url)
    w3 = Web3(provider)
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

    account = '0xba86aF256A7CBfa61bf6293861298DAe8aBb84F6'
    nonce = w3.eth.getTransactionCount(account)
    password = 'password'
    with open('./keystore/UTC--2020-05-28T22-40-35.248279000Z--ba86af256a7cbfa61bf6293861298dae8abb84f6') as keyfile:   # noqa: E501
        encrypted_key = keyfile.read()
    private_key = w3.eth.account.decrypt(encrypted_key, password)
    gas_price = w3.eth.generateGasPrice()
    transaction = {
        'to': w3.toChecksumAddress(recipient),
        'value': int(amount),
        'gas': int(1.5*10**6),
        'gasPrice': gas_price,
        'nonce': nonce,
        'chainId': RINKEBY_CHAIN_ID
    }
    tx = w3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = w3.eth.sendRawTransaction(tx.rawTransaction)
    print(tx_hash.hex())
    import pdb; pdb.set_trace()


@task
def extract_private_key(c, path, password):
    """
    get the plaintext private key for an ethereum account created using the
    'geth account new --datadir=.' cmd
    """
    with open(path) as keyfile:
        encrypted_key = keyfile.read()
    private_key = W3.eth.account.decrypt(encrypted_key, password)
    print(Web3.toHex(private_key))


@task
def get_contract_address_by_abi(c, abi_path):
    path = Path(abi_path).resolve()
    with path.open() as fp:
        abi = json.loads(fp.read())
    contract = W3.eth.contract(abi=abi)
    import pdb; pdb.set_trace()
    print(contract)


@task
def get_revert_reason(c, tx_hash):
    tx = W3.eth.getTransaction(tx_hash)
    tx_dict = dict(tx)
    # print(tx)
    receipt = W3.eth.waitForTransactionReceipt(tx.hash)
    # contract = receipt.to
    tx_json = json.loads(json.dumps(tx_dict, cls=HexJsonEncoder))
    # import pdb; pdb.set_trace()
    tx_json.update({'chainId': W3.eth.chainId})
    code = W3.eth.call(tx_json, receipt['blockNumber']).hex()
    print(bytes.fromhex(code[code.find('b')+1:].rstrip('0')).decode('utf-8'))


class Contract:
    def __init__(self, addr, abi, csv):
        self.address = Web3.toChecksumAddress(addr)
        with Path(abi).open() as fp:
            self.abi = json.load(fp)
        self.csv = Path(csv)


@task
def get_logs(c, tx_hash):
    # kovan_synthetix_contract_addr = '0x404469525f6Ab4023Ce829D8F627d424D3986675'   # noqa: E501
    tx = W3.eth.getTransaction(tx_hash)
    receipt = W3.eth.waitForTransactionReceipt(tx.hash)
    with open('./synthetix/Synthetix.json') as fp:
        abi = json.load(fp)
    contract = W3.eth.contract(address=receipt.to, abi=abi)
    import pdb; pdb.set_trace()
