import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request
'''
区块链中每个区块包含属性:索引(index),Unix时间戳(timestamp),交易列表(transactions),工作量证明以及前一个区块的Hash值。
例如：
block = {
    'index': 1, #索引
    'timestamp': 1506057125.900785, #时间戳
    'transactions': [ #交易
        {
            'sender': "8527147fe1f5426f9dd545de4b27ee00",
            'recipient': "a77f5cdfa2934df3954a5c7c7da5df1f",
            'amount': 5,
        }
    ],
    'proof': 324984774000, #工作量证明
    'previous_hash': "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824" #前一个区块的Hash值
}

'''


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # 生成一个创世块
        self.new_block(proof=100, previous_hash=1)

    def new_block(self, proof, previous_hash=None):
        # 生成一个新的区块并添加到区块链
        """
            生成新块
            :param proof: <int> The proof given by the Proof of Work algorithm
            :param previous_hash: (Optional) <str> Hash of previous Block
            :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]), #前一区块的Hash值或创世块
        }

        # 重置交易
        self.current_transactions = []

        self.chain.append(block)
        return block
        # pass

    def new_transaction(self, sender, recipient, amount):
        # 新增一个交易到交易列表
        """
            生成新交易信息，信息将加入到下一个待挖的区块中
            :param sender: <str> Address of the Sender
            :param recipient: <str> Address of the Recipient
            :param amount: <int> Amount
            :return: <int> The index of the Block that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1
        # pass

    @staticmethod
    def hash(block):
        # 区块的哈希
        """
            生成块的 SHA-256 hash值
            :param block: <dict> Block
            :return: <str>
        """

        # 我们必须确保字典是有序的，否则我们将有不一致的哈希值
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
        #pass

    @property
    def last_block(self):
        # 返回区块链最后一个区块
        return self.chain[-1]
        # pass

    def proof_of_work(self, last_proof):
        """
            简单的工作量证明:
             - 查找一个 p' 使得 hash(pp') 以4个0开头
             - p 是上一个块的证明,  p' 是当前的证明
            :param last_proof: <int>
            :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
            验证证明: 是否hash(last_proof, proof)以4个0开头?
            :param last_proof: <int> Previous Proof
            :param proof: <int> Current Proof
            :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# 实例化节点,创建一个节点
app = Flask(__name__)

# 为该节点生成一个随机的名字
node_identifier = str(uuid4()).replace('-','')

# 实例化Blockchain类
blockchain = Blockchain()

# 创建/mine GET接口
@app.route('/mine', methods=['GET'])
def mine():
    # 运行工作证明算法以获得下一个证明
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # 给工作量证明的节点提供奖励.
    # 发送者为 "0" 表明是新挖出的币
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # 通过将其添加到链中来生成新块
    block = blockchain.new_block(proof)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }

    return jsonify(response), 200
    # return "We'll mine a new Block"

# 创建/transactions/new POST接口，可以给接口发送交易数据
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # 检查必填字段是否在POST中
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    #创建一个新的交易
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201
    # return "We'll add a new transaction"

# 创建/chain 接口，返回整个区块链
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

# 服务运行在端口5000上
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)