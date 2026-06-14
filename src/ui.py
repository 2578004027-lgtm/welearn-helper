"""
WeLearn 网课助手 - 终端界面
"""

import sys
import os
import random

if sys.platform == 'win32':
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    ctypes.windll.kernel32.SetConsoleCP(65001)

from colorama import init, Fore, Style
init(autoreset=True)

# ---- 配色 ----
C = Fore.CYAN
G = Fore.GREEN
R = Fore.RED
Y = Fore.YELLOW
W = Fore.LIGHTWHITE_EX
M = Fore.LIGHTMAGENTA_EX
B = Style.BRIGHT
RS = Style.RESET_ALL


def show_banner(mode: str):
    print(f"""
{C}{B}    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║       ██╗    ██╗███████╗██╗     ███████╗ █████╗ ██████╗ ███╗   ██╗
    ║       ██║    ██║██╔════╝██║     ██╔════╝██╔══██╗██╔══██╗████╗  ██║
    ║       ██║ █╗ ██║█████╗  ██║     █████╗  ███████║██████╔╝██╔██╗ ██║
    ║       ██║███╗██║██╔══╝  ██║     ██╔══╝  ██╔══██║██╔══██╗██║╚██╗██║
    ║       ╚███╔███╔╝███████╗███████╗███████╗██║  ██║██║  ██║██║ ╚████║
    ║        ╚══╝╚══╝ ╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
    ║                                                                  ║
    ║{M}{B}              ◆◇◆  网 课 助 手 - {mode}  ◆◇◆                {C}
    ║{Y}{B}                         v1.0                                    {C}
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║{W}       开发者 : 缘                                                {C}
    ║{W}       QQ     : 2578004027                                        {C}
    ║{W}       邮箱   : 2578004027@qq.com                                  {C}
    ║                                                                  ║
    ║{W}  适用平台: WeLearn (welearn.sflep.com)                            {C}
    ║{G}  仓库地址: github.com/2578004027-lgtm/welearn-helper              {C}
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝{RS}
""")


def sep():
    print(f'{C}{"─" * 70}{RS}')


def ok(msg: str):
    print(f'{G}{B}[√]{RS} {msg}')


def fail(msg: str):
    print(f'{R}{B}[×]{RS} {msg}')


def info(msg: str):
    print(f'{C}[*]{RS} {msg}')


def prompt(msg: str) -> str:
    return input(f'{Y}{msg}{RS}').strip()


def show_course_list(courses: list):
    for i, c in enumerate(courses, 1):
        per = int(c.get('per', 0))
        color = G if per >= 80 else (Y if per >= 50 else R)
        print(f'  {W}[NO.{i:>2d}]{RS}  {color}进度 {per:>3d}%{RS}  {c.get("name","")}')


def show_unit_list(units: list):
    print(f'\n  {Y}[NO. 0]{RS}  全部单元')
    for i, u in enumerate(units, 1):
        inf = u.get('info', {})
        name = inf.get('unitname', '?')
        if inf.get('iscomplete') == 'completed':
            tag = f'{G}[已完成]{RS}'
        elif inf.get('isvisible', 'true') == 'true':
            tag = f'{W}[待完成]{RS}'
        else:
            tag = f'{R}[未开放]{RS}'
        print(f'  {W}[NO.{i:>2d}]{RS}  {tag}  {name}')


def show_result_course(w1_ok, w1_fail, w2_ok, w2_fail):
    print(f'''
{C}{B}╔══════════════════════════════════════════════════════════════╗
║{G}{B}                      全 部 完 成 !                           {C}{B}║
╠══════════════════════════════════════════════════════════════╣
║{W}  方式1 (startsco):   成功 {G}{w1_ok:>4}{W}  /  失败 {R}{w1_fail:>4}{W}                   {C}{B}║
║{W}  方式2 (savescoinfo): 成功 {G}{w2_ok:>4}{W}  /  失败 {R}{w2_fail:>4}{W}                   {C}{B}║
╠══════════════════════════════════════════════════════════════╣
║{W}  开发者: 缘        QQ: 2578004027                           {C}{B}║
║{W}  邮箱: 2578004027@qq.com                                    {C}{B}║
╚══════════════════════════════════════════════════════════════╝{RS}
''')


def show_result_sleep(wrong, total):
    print(f'''
{C}{B}╔══════════════════════════════════════════════════════════════╗
║{G}{B}                      全 部 完 成 !                           {C}{B}║
╠══════════════════════════════════════════════════════════════╣
║{W}  总单元: {G}{total:>4}{W}        失败: {R}{wrong:>4}{W}                              {C}{B}║
╠══════════════════════════════════════════════════════════════╣
║{W}  开发者: 缘        QQ: 2578004027                           {C}{B}║
║{W}  邮箱: 2578004027@qq.com                                    {C}{B}║
╚══════════════════════════════════════════════════════════════╝{RS}
''')


def parse_number_list(user_input: str, max_val: int) -> list:
    """解析 '1,2,3' 或 '0' 格式的输入"""
    s = user_input.strip()
    if s == '0':
        return list(range(max_val))
    result = []
    for part in s.split(','):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < max_val:
                result.append(idx)
    return sorted(set(result))


def parse_range(user_input: str, max_val: int = 100) -> tuple:
    """解析 '70,100' 或 '80' 格式的范围输入"""
    s = user_input.strip()
    if ',' in s:
        a, b = s.split(',', 1)
        return int(a.strip()), int(b.strip()), True
    return int(s), int(s), False
