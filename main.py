#!/usr/bin/env python3
"""
WeLearn 网课助手 v1.0
开发者: 缘  QQ: 2578004027  邮箱: 2578004027@qq.com

用法: python main.py
"""

import time
import threading
from random import randint

from src.core import Session, CourseInfo, TaskRunner, IdleRunner, check_license
import src.ui as ui


def run_course(session: Session):
    """课程模式 — 刷练习题"""
    courses = CourseInfo(session).list_all()
    if not courses:
        ui.fail('未找到课程！'); return
    ui.ok(f'共 {len(courses)} 门课程')
    ui.show_course_list(courses)

    idx = int(ui.prompt('\n请选择课程序号: ')) - 1
    if not (0 <= idx < len(courses)):
        ui.fail('序号错误！'); return
    cid = courses[idx]['cid']

    uid, classid = CourseInfo(session).get_detail(cid)
    if not uid:
        ui.fail('无法提取课程信息！'); return

    units = CourseInfo(session).get_units(cid)
    ui.show_unit_list(units)

    selected = ui.parse_number_list(
        ui.prompt('\n请选择单元（逗号分隔，0=全部）: '), len(units))
    if not selected:
        ui.fail('未选择任何单元！'); return

    lo, hi, is_rand = ui.parse_range(
        ui.prompt('\n正确率（如 100 或 70,100）: '))

    runner = TaskRunner(session, cid, uid, classid)
    ui.sep()
    ui.info(f'开始刷课 | {len(selected)} 单元 | '
            f'正确率: {lo}%~{hi}%（随机）' if is_rand else f'{lo}%（固定）')
    ui.sep()

    w1_ok = w1_fail = w2_ok = w2_fail = 0

    for unit_idx in selected:
        u = units[unit_idx]
        inf = u.get('info', {})
        name = inf.get('unitname', '?')

        if inf.get('isvisible', 'true') == 'false':
            ui.fail(f'[跳过] {name} (未开放)'); continue
        if inf.get('iscomplete') == 'completed':
            ui.ok(f'[已完成] {name}'); continue

        ui.info(f'[处理中] {name}')

        for sco in runner.fetch_sco(unit_idx):
            sid = sco.get('id', '')
            if not sco.get('isvisible', True): continue

            acc = randint(lo, hi) if is_rand else lo
            ok1, ok2 = runner.submit(sid, acc)

            w1_ok += ok1; w1_fail += not ok1
            w2_ok += ok2; w2_fail += not ok2

            s1 = f'{ui.G}OK{ui.RS}' if ok1 else f'{ui.R}FAIL{ui.RS}'
            s2 = f'{ui.G}OK{ui.RS}' if ok2 else f'{ui.R}FAIL{ui.RS}'
            c = ui.G if acc >= 80 else (ui.Y if acc >= 60 else ui.R)
            print(f'  {sid[:12]:<12} 正确率={c}{acc:>3}%{ui.RS}  w1={s1}  w2={s2}')

    ui.show_result_course(w1_ok, w1_fail, w2_ok, w2_fail)


def run_sleep(session: Session):
    """时长模式 — 刷学习时间"""
    courses = CourseInfo(session).list_all()
    if not courses:
        ui.fail('未找到课程！'); return
    ui.ok(f'共 {len(courses)} 门课程')
    ui.show_course_list(courses)

    idx = int(ui.prompt('\n请选择课程序号: ')) - 1
    if not (0 <= idx < len(courses)):
        ui.fail('序号错误！'); return
    cid = courses[idx]['cid']

    uid, classid = CourseInfo(session).get_detail(cid)
    if not uid:
        ui.fail('无法提取课程信息！'); return

    units = CourseInfo(session).get_units(cid)
    ui.show_unit_list(units)

    selected = ui.parse_number_list(
        ui.prompt('\n请选择单元（逗号分隔，0=全部）: '), len(units))
    if not selected:
        ui.fail('未选择任何单元！'); return

    lo, hi, is_rand = ui.parse_range(
        ui.prompt('\n学习时长（秒，如 30 或 10,30）: '), max_val=9999)
    n = int(ui.prompt('线程数（1-10）: ') or '3')
    n = max(1, min(10, n))

    runner = IdleRunner(session, cid, uid, classid)
    ui.sep()
    ui.info(f'开始刷时长 | {len(selected)} 单元 | {n} 线程 | '
            f'时长: {lo}~{hi}秒（随机）' if is_rand else f'{lo}秒（固定）')
    ui.sep()

    wrong = [0]
    running = [True]
    lock = threading.Lock()

    def process_one(unit_idx):
        u = units[unit_idx]
        name = u.get('info', {}).get('unitname', '')
        dur = randint(lo, hi) if is_rand else lo
        for sco in runner.fetch_sco(unit_idx):
            if not running[0]: return
            if not runner.submit(sco.get('id', ''), dur):
                with lock: wrong[0] += 1
        ui.ok(f'[完成] {name} ({dur}秒)')

    workers = []
    for idx in selected:
        t = threading.Thread(target=process_one, args=(idx,), daemon=True)
        workers.append(t)
        t.start()
        while sum(1 for t in workers if t.is_alive()) >= n:
            time.sleep(0.2)

    for t in workers:
        t.join()
    running[0] = False

    ui.show_result_sleep(wrong[0], len(selected))


def main():
    check_license()

    # 选模式
    print(f"""
{ui.C}{ui.B}    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║       ██╗    ██╗███████╗██╗     ███████╗ █████╗ ██████╗ ███╗   ██╗
    ║       ██║    ██║██╔════╝██║     ██╔════╝██╔══██╗██╔══██╗████╗  ██║
    ║       ██║ █╗ ██║█████╗  ██║     █████╗  ███████║██████╔╝██╔██╗ ██║
    ║       ██║███╗██║██╔══╝  ██║     ██╔══╝  ██╔══██║██╔══██╗██║╚██╗██║
    ║       ╚███╔███╔╝███████╗███████╗███████╗██║  ██║██║  ██║██║ ╚████║
    ║        ╚══╝╚══╝ ╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
    ║                                                                  ║
    ║{ui.M}{ui.B}                    ◆◇◆  网 课 助 手  ◆◇◆                      {ui.C}
    ║{ui.Y}{ui.B}                         v1.0                                    {ui.C}
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║{ui.W}       开发者 : 缘         QQ: 2578004027                       {ui.C}
    ║{ui.W}       邮箱   : 2578004027@qq.com                               {ui.C}
    ║                                                                  ║
    ║{ui.W}  适用平台: WeLearn (welearn.sflep.com)                         {ui.C}
    ║{ui.G}  仓库地址: github.com/2578004027-lgtm/welearn-helper           {ui.C}
    ║                                                                  ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║{ui.W}       [1] 课程模式  — 自动完成练习题，自定义正确率            {ui.C}
    ║{ui.W}       [2] 时长模式  — 多线程模拟学习时间，飞速挂机            {ui.C}
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝{ui.RS}
""")

    mode = ui.prompt('请选择模式 [1/2]: ')
    if mode not in ('1', '2'):
        ui.fail('无效选择！')
        return

    phone = ui.prompt('请输入手机号: ')
    pwd = ui.prompt('请输入密码: ')
    ui.info('正在登录...')

    session = Session()
    if not session.login(phone, pwd):
        ui.fail('登录失败！请检查账号密码。')
        return
    ui.ok('登录成功！')

    if mode == '1':
        run_course(session)
    else:
        run_sleep(session)


if __name__ == '__main__':
    main()
