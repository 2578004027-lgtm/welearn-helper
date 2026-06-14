"""
WeLearn 网课助手 - 核心模块
"""

import time
import base64
import json
import re
import os
import hashlib
import uuid
import platform
import requests
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict


# ============================================================
# 授权验证
# ============================================================

PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuod4sH6ok25AVOlCHn60
X5MSWw0HC8IUmwQYNLzwZKwQEbXO2jffg2eXIvx3GbsEw7HIpfMXYnalSFxnx6c5
UlDaoeRLaGjtxYnz8Ls4A/PHm8S3E4Wf/KTksjUsv4gCeq8VnotroGhMOMkosbc9
rsHQbHT0F4/Vq3jWe0ZmYxj7235woovqdYVToetq60UAgtIBZBREX4NJkP5yyqn3
VkEnAAiSTEb+dJmE9HU1yoceNl8YH8ZMHYajO15g9W460aPhwACKjI15m4/Zu/XM
UFRHyg60nKuhiKIZTsYcKBkf9y75TSaJ+x77fZXXPpe9HAnR5CLLKta6GRvGC2yU
ZwIDAQAB
-----END PUBLIC KEY-----"""

TIME_SERVERS = ['https://www.baidu.com', 'https://www.qq.com', 'https://www.aliyun.com']


def _machine_id() -> str:
    raw = f'{uuid.getnode()}-{platform.system()}-{platform.processor()}'
    return hashlib.sha256(raw.encode()).hexdigest()


def _network_time() -> Optional[float]:
    for url in TIME_SERVERS:
        try:
            r = requests.get(url, timeout=3)
            ds = r.headers.get('Date', '')
            if ds:
                dt = datetime.strptime(ds, '%a, %d %b %Y %H:%M:%S GMT')
                return (dt + timedelta(hours=8)).timestamp()
        except Exception:
            continue
    return None


def verify_license(lic_path: str = 'license.lic') -> Tuple[bool, str]:
    """
    验证授权文件。
    返回 (是否有效, 消息)
    """
    if not os.path.exists(lic_path):
        return False, '未找到授权文件 license.lic'

    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        with open(lic_path, 'r') as f:
            lic = json.load(f)

        payload_bytes = base64.b64decode(lic['payload'])
        signature = base64.b64decode(lic['sign'])

        pubkey = serialization.load_pem_public_key(PUBLIC_KEY)
        pubkey.verify(signature, payload_bytes, padding.PKCS1v15(), hashes.SHA256())

        payload = json.loads(payload_bytes)

        if payload.get('machine') != _machine_id():
            return False, '机器码不匹配'

        net_ts = _network_time()
        if net_ts is None:
            return False, '无法连接网络，请检查网络后重试'

        if net_ts > payload.get('expire', 0):
            return False, '授权已过期'

        return True, '授权有效'

    except Exception as e:
        return False, f'授权文件无效 ({e})'


def check_license():
    """启动时检查授权，失败则退出"""
    ok, msg = verify_license()
    if ok:
        return
    print(f'\n[!] 授权验证失败: {msg}')
    print(f'    机器码: {_machine_id()}')
    print(f'    请购买授权后将 license.lic 放在程序目录下\n')
    input('按回车键退出...')
    exit(1)


# ============================================================
# 密码编码
# ============================================================

def encode_password(password: str) -> Tuple[str, int]:
    t0 = int(time.time() * 1000)
    p_bytes = password.encode('utf-8')
    v = (t0 >> 16) & 0xFF
    for b in p_bytes:
        v ^= b
    t1 = v + 100
    payload = t1.to_bytes(8, 'big') + p_bytes
    return base64.b64encode(payload).decode('ascii'), t1


# ============================================================
# 会话管理
# ============================================================

class Session:
    UA_LEGACY = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.34'
    )
    UA_MODERN = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
    )

    def __init__(self):
        self._s = requests.Session()

    def login(self, phone: str, password: str) -> bool:
        encoded, ts = encode_password(password)
        self._s.get('https://sso.sflep.com/idsvr/login.html',
                     headers={'User-Agent': self.UA_LEGACY})
        self._s.post('https://sso.sflep.com/idsvr/account/login',
                     data={'account': phone, 'pwd': encoded, 'ts': str(ts)},
                     headers={'User-Agent': self.UA_LEGACY})
        self._s.get('https://welearn.sflep.com/user/prelogin.aspx'
                     '?loginret=http%3a%2f%2fwelearn.sflep.com%2fuser%2floginredirect.aspx',
                     headers={'Referer': 'https://welearn.sflep.com/student/index.aspx',
                              'User-Agent': self.UA_MODERN})
        resp = self._s.get('https://welearn.sflep.com/student/index.aspx',
                           headers={'User-Agent': self.UA_MODERN})
        return '我的主页' in resp.text

    def get(self, url: str, referer: str = '') -> str:
        h = {'User-Agent': self.UA_MODERN}
        if referer: h['Referer'] = referer
        return self._s.get(url, headers=h).text

    def post(self, url: str, data: str = '') -> str:
        return self._s.post(url, data=data,
                            headers={'User-Agent': self.UA_MODERN}).text


# ============================================================
# 课程信息
# ============================================================

class CourseInfo:
    def __init__(self, session: Session):
        self._s = session

    def list_all(self) -> List[Dict]:
        raw = self._s.get('https://welearn.sflep.com/ajax/authCourse.aspx?action=gmc',
                           'https://welearn.sflep.com/student/index.aspx')
        try:
            return json.loads(raw + '"clist":[]}').get('clist', [])
        except json.JSONDecodeError:
            return []

    def get_detail(self, cid: str) -> Tuple[str, str]:
        html = self._s.get(
            f'https://welearn.sflep.com/student/course_info.aspx?cid={cid}',
            'https://welearn.sflep.com/student/index.aspx')
        uid = re.search(r'"uid":(\d+)', html)
        cid_m = re.search(r'"classid":"(\d+)"', html)
        return (uid.group(1) if uid else '', cid_m.group(1) if cid_m else '')

    def get_units(self, cid: str) -> List[Dict]:
        raw = self._s.post('https://welearn.sflep.com/ajax/StudyStat.aspx',
                            f'cid={cid}')
        try:
            return json.loads(raw).get('courseunits', [])
        except json.JSONDecodeError:
            return []


# ============================================================
# 任务执行器 - 课程版
# ============================================================

class TaskRunner:
    SCO_API = 'https://welearn.sflep.com/Ajax/SCO.aspx'

    def __init__(self, session: Session, cid: str, uid: str, classid: str):
        self._s = session
        self.cid, self.uid, self.classid = cid, uid, classid

    def fetch_sco(self, unit_idx: int) -> List[Dict]:
        url = (f'https://welearn.sflep.com/ajax/StudyStat.aspx'
               f'?action=scoLeaves&cid={self.cid}&uid={self.uid}'
               f'&unitidx={unit_idx}&classid={self.classid}')
        try:
            return json.loads(self._s.get(url)).get('data', [])
        except json.JSONDecodeError:
            return []

    def submit(self, sco_id: str, accuracy: int) -> Tuple[bool, bool]:
        r1 = self._s.post(self.SCO_API,
            f'action=startsco160928&cid={self.cid}&scoid={sco_id}&uid={self.uid}')
        r2 = self._s.post(self.SCO_API,
            f'action=savescoinfo160928&cid={self.cid}&scoid={sco_id}'
            f'&uid={self.uid}&progress=1.0&crate={accuracy}'
            f'&status=completed&cstatus=passed&trycount=0')
        return '"ret":0' in r1, '"ret":0' in r2


# ============================================================
# 任务执行器 - 时长版
# ============================================================

class IdleRunner:
    SCO_API = 'https://welearn.sflep.com/Ajax/SCO.aspx'

    def __init__(self, session: Session, cid: str, uid: str, classid: str):
        self._s = session
        self.cid, self.uid, self.classid = cid, uid, classid

    def fetch_sco(self, unit_idx: int) -> List[Dict]:
        url = (f'https://welearn.sflep.com/ajax/StudyStat.aspx'
               f'?action=scoLeaves&cid={self.cid}&uid={self.uid}'
               f'&unitidx={unit_idx}&classid={self.classid}')
        try:
            return json.loads(self._s.get(url)).get('data', [])
        except json.JSONDecodeError:
            return []

    def submit(self, sco_id: str, duration: int) -> bool:
        self._s.post(self.SCO_API,
            f'action=startstudy&cid={self.cid}&scoid={sco_id}&uid={self.uid}')
        time.sleep(duration)
        resp = self._s.post(self.SCO_API,
            f'action=savescoinfo160928&cid={self.cid}&scoid={sco_id}'
            f'&uid={self.uid}&progress=1.0&crate=100'
            f'&status=completed&cstatus=passed&trycount=0')
        return '"ret":0' in resp
