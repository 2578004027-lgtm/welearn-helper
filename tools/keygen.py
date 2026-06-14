#!/usr/bin/env python3
"""
License 生成工具
用于替换 exe 内置公钥后自签 license.lic

用法:
  python tools/keygen.py genkey       生成密钥对
  python tools/keygen.py license      签发 license.lic
"""

import sys
import os
import json
import base64
import hashlib
import uuid
import platform
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


def machine_id() -> str:
    raw = f'{uuid.getnode()}-{platform.system()}-{platform.processor()}'
    return hashlib.sha256(raw.encode()).hexdigest()


def cmd_genkey():
    print('[*] 生成 RSA-2048 密钥对...')
    pri = rsa.generate_private_key(65537, 2048)
    pub = pri.public_key()

    pri_pem = pri.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open('private.key', 'wb') as f: f.write(pri_pem)
    with open('public.key', 'wb') as f: f.write(pub_pem)
    print('[√] 密钥已保存: private.key / public.key\n')
    print('将此公钥替换 src/core.py 中的 PUBLIC_KEY，然后重新打包即可：')
    print('-' * 60)
    print(pub_pem.decode())
    print('-' * 60)


def cmd_license(days: int = 3650):
    if not os.path.exists('private.key'):
        print('[×] 找不到 private.key，请先运行 genkey')
        return

    with open('private.key', 'rb') as f:
        pri = serialization.load_pem_private_key(f.read(), password=None)

    payload_dict = {
        'machine': machine_id(),
        'expire': int((datetime.now() + timedelta(days=days)).timestamp())
    }
    payload_bytes = json.dumps(payload_dict).encode()
    sig = pri.sign(payload_bytes, padding.PKCS1v15(), hashes.SHA256())

    lic = {
        'payload': base64.b64encode(payload_bytes).decode(),
        'sign': base64.b64encode(sig).decode()
    }

    with open('license.lic', 'w') as f:
        json.dump(lic, f, indent=2)

    exp = datetime.fromtimestamp(payload_dict['expire'])
    print(f'[√] license.lic 已生成')
    print(f'    机器码: {payload_dict["machine"]}')
    print(f'    到期日: {exp.strftime("%Y-%m-%d %H:%M:%S")}（{days}天）')
    print()
    print('[!] 注意: 需先替换 exe 中的公钥为你的公钥，否则 license 无效！')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python tools/keygen.py genkey|license [days]')
    elif sys.argv[1] == 'genkey':
        cmd_genkey()
    elif sys.argv[1] == 'license':
        cmd_license(int(sys.argv[2]) if len(sys.argv) > 2 else 3650)
