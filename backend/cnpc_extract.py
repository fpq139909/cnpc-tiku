#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
党建云题目提取工具（命令行版）

支持三种模板（给定浏览器里 detailedInfo.html?... 的完整网址，自动解析并提取）：
  - oneMonthLearning      月月学       （m.dj.cnpc.com.cn）
  - projectLearning       项目学习/专题学（mobilenew.xianfengdangjian.com.cn）
  - oneMonthLearningXxyd  学习用典     （mobilenew.xianfengdangjian.com.cn）

流程：
  - 月月学 / 学习用典：getQuesBank(activeMonths|activeId) -> questionId -> queryTestInfo(id)
  - 项目学习：          queryTestInfo(id)  （一次调用）
  响应均用内嵌 RSA 私钥 + AES-ECB 解密（同一套先锋党建系统）。

用法：
  python cnpc_extract.py "完整网址"
  python cnpc_extract.py "完整网址" -o 输出.txt
  python cnpc_extract.py --url "完整网址" --md
  python cnpc_extract.py "完整网址" --md    # 导出 Markdown
"""

import argparse
import base64
import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime

# 需要时自动安装依赖
try:
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto.Util.Padding import unpad
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pycryptodome", "-q"])
    from Crypto.Cipher import AES, PKCS1_v1_5
    from Crypto.PublicKey import RSA
    from Crypto.Util.Padding import unpad

# 内嵌 RSA 私钥（来自 global.js，用于解密响应头里的 AES 密钥；三种模板共用）
PRIVATE_KEY_PEM = """-----BEGIN RSA PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCC+rpzABi51o4O
1B4XGM9sKh6ccdla6S4j9pqFu97aN+Hrh46VWVC/lczYvOwy/Wqhp1nOjtLcM6BQ
Gi1sd2G7jY+L3ttvk7ipqgSYoG7fch/90n7r1CCaPjHgRxZnme1RQH/5sfactcft
6Yv2E+w2NjMZ96kAN0SBjqUZj/p2+p9r4uKD1+frlyJ2gBlLnYyT1ttjIgb2ei00
HMPalSt5Iz+FjpS6ikPCvEd2ibKQg1kX9C4BSI+vLPEOviFqGwT6WbAi1XVSVq5S
HvoDaUdjKQpgp0/kyIOUFnZiUAMmM8LNEOQ0qmUFXNzEW43UlctUiP1ajNMFw8/A
StKWaLO7AgMBAAECggEAUwEJv29EPCEYDZWnLAPxDx7yHzqW/+Hd97SD4FRauffIG
DbjyQm8/my0UHYJSZcHSEKBy0D/p8Sfx6OPPbm6Gd1wJreoYGFBGWRBXWfuW3Q7i
eMnw9O+hYD8oqDqNeV6W4+AioCZRF5+wOrMY7nka8aVQ9OLKjPcGi6Huldf5p2sq
3eCp+WBq9XdEzTxo1mnrl9NEou1rVvidkbjbEoXgmE7SQRhvtnu9orksMwOAhRGY
nnwa8J57SAFBxpUEYDk49eW6OMThLkdqr8OSEJX5VY0rdW6AfFF6M1ZjUh9qLQuP
D3pr0nldCk01rwkfhIadZb3v3b+/XrGpDVK/6RkYQKBgQC/y0grIVW1EQCOnyVNb
Rqu/+RZqXzHilPvEgx7ndmiJfYhnlVmuT0Ze0drUNDPrJwiTpvQgiH7bOW8JkUOx
i5pJnvlBVshhOhziJtgr42jqQPs++wpYBdzLt/ewu8/g8RLwO0B3TJsl3JwXwqtJ
ETW+4rzSl7TT1K2AVOA6beY3QKBgQCu06P5SwkOO11YlkafcBUtqM/xYSBzairU
a7n6DyKGQ8MJq/QA49CxKt59WR/uBX6ryRJsgGPpfv48urdIwraZFhauiUjwg+dG
Om7CL68o5PvN2p6mQvB6uPkiw1aJ4i8Fh7BcQbNDRXbINsKLkEwRw4VRGxwiDht
F/AnjwPZpdwKBgDP8gd9O9dBSf3gpIw9Nl4H/0oGLM0tS71VJ6yBGtQsChyitpjB
l3W3ewIkSKsdf3iJedFWcMGHaLptFNErA5SuTRtnZDc6UG/3U9WjLrPTDh1DhKC4
+4ZxTBFN5OyhYKwjtjlCHCHfuxRI4cMhloFM1c4BmlDVqttyml1/F+gHxAoGBAJ8I
1ZQ0hvNUW3D3mxz0l79mXmskwKFdBcMgkBiCZhSfVa/ZpWid1L0l0ylRxvL+OqHI
kqLzFHBW3q2d6Jce0X5nEpEJP7nTM7K1+wVY3U0lKE61vjZelGX/GFtgOLvLbpzo
Ny1lcs4SRaCR991/kUNjikYilDAChxrd0J1HbqC3AoGACL/mUmc/GBM1Qk4BxQj4
b8ZrIbwwmOzn73sEaDzEUZssJ/N0joTro1Wa3XFLzl8U402sbAXX+6LPJ3WU7q+2
/sNhDJ2kfBMqdvcDDGtdVDi49vkExnMKtMdgdW2Q9eWPZYvruMVWIyJvw1XA1ykT
Re4Fy/vcwxO+I6Q4Y8mKsAM=
-----END RSA PRIVATE KEY-----"""

# 题型编码 -> 中文名
TYPE_NAME = {
    "01": "单选题",
    "02": "多选题",
    "03": "判断题",
}

# 模板 -> 中文标题
TEMPLATE_NAME = {
    "oneMonthLearning": "月月学",
    "projectLearning": "专题学",
    "oneMonthLearningXxyd": "学习用典",
}

# 需要两步的模板：先 getQuesBank 拿 questionId，再 queryTestInfo
# 值为 (getQuesBank 路径, 请求体参数名)
TEMPLATE_BANK = {
    "oneMonthLearning": ("/party/homePage/learningEachMonth/getQuesBank", "activeMonths"),
    "oneMonthLearningXxyd": ("/party/homePage/learningEachMonthXxyd/getQuesBank", "activeId"),
}
# 通用题目详情接口（三种模板共用，参数名均为 id）
QUERY_TEST_INFO = "/party/activityExam/onlineExam/queryTestInfo"


def now_beijing():
    """返回当前北京时间字符串 YYYYMMDDHHMMSS。"""
    try:
        from zoneinfo import ZoneInfo
        dt = datetime.now(ZoneInfo("Asia/Shanghai"))
    except Exception:
        dt = datetime.utcnow() + __import__("datetime").timedelta(hours=8)
    return dt.strftime("%Y%m%d%H%M%S")


def parse_url(url):
    """从完整网址解析出 origin、模板类型、rx_token 与各参数。"""
    p = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(p.query)
    origin = f"{p.scheme}://{p.netloc}"
    parts = [x for x in p.path.split("/") if x]
    template = None
    if "template" in parts:
        i = parts.index("template")
        if i + 1 < len(parts):
            template = parts[i + 1]
    return {
        "origin": origin,
        "template": template,
        "rx_token": (qs.get("rx_token") or [None])[0],
        "activeMonths": (qs.get("activeMonths") or [None])[0],
        "activeId": (qs.get("activeId") or [None])[0],
        "id": (qs.get("id") or [None])[0],
    }


def decrypt_rsa(encrypted_b64):
    encrypted = base64.b64decode(encrypted_b64)
    key = RSA.import_key(PRIVATE_KEY_PEM)
    cipher = PKCS1_v1_5.new(key)
    out = b""
    for i in range(0, len(encrypted), 256):
        out += cipher.decrypt(encrypted[i:i + 256], b"")
    return out.decode("utf-8")


def decrypt_aes(key_b64, encrypted_b64):
    key = base64.b64decode(key_b64)
    data = base64.b64decode(encrypted_b64)
    cipher = AES.new(key, AES.MODE_ECB)
    return unpad(cipher.decrypt(data), AES.block_size).decode("utf-8")


def call_api(base_url, path, body_obj, rx_token):
    """POST 调用接口，返回 (data_dict, error_msg)。base_url 为网址 origin。"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "rxToken": rx_token,
        "res": "10",
        "source": "2",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
        "Origin": base_url,
        "Referer": base_url + "/sydj-mobile/webcontent/template/oneMonthLearning/detailedInfo.html",
    }
    req = urllib.request.Request(
        base_url + path,
        data=json.dumps(body_obj).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
        bk = resp.headers.get("bk", "")
        body = resp.read().decode("utf-8").strip()
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}：{e.read().decode('utf-8', 'ignore')[:200]}"
    except Exception as e:
        return None, f"网络错误：{e}"

    if not bk or not body:
        return None, "接口未返回加密数据（可能令牌已失效，请重新从浏览器复制最新网址）"

    try:
        aes_key = decrypt_rsa(bk)
        plain = decrypt_aes(aes_key, body)
        return json.loads(plain), None
    except Exception as e:
        return None, f"解密失败：{e}"


def extract(parsed):
    """按模板分发，返回 (meta, questions, name, error)。"""
    template = parsed.get("template")
    origin = parsed.get("origin")
    rx = parsed.get("rx_token")
    if not rx:
        return None, None, None, "未能从网址解析出 rx_token，请确认复制的是完整的 detailedInfo.html?... 链接。"
    if template not in TEMPLATE_NAME:
        return None, None, None, f"不支持的模板类型：{template}（仅支持月月学 / 项目学习 / 学习用典）"

    # 第一步：获取 questionId（项目学习无需此步，直接用 URL 的 id）
    if template == "projectLearning":
        qid = parsed.get("id")
        if not qid:
            return None, None, None, "项目学习链接缺少 id 参数"
    else:
        bank_path, bank_param = TEMPLATE_BANK[template]
        bval = parsed.get(bank_param)
        if not bval:
            return None, None, None, f"链接缺少 {bank_param} 参数"
        data1, err = call_api(origin, bank_path, {bank_param: bval}, rx)
        if err:
            return None, None, None, err
        if not (data1.get("success") and data1.get("data")):
            return None, None, None, (data1.get("message") or "获取题库失败") + "（令牌可能已失效，请重新复制最新网址）"
        qid = data1["data"].get("questionId")
        if not qid:
            return None, None, None, "未返回 questionId"

    # 第二步：获取题目详情（三种模板共用 queryTestInfo，参数为 id）
    data2, err = call_api(origin, QUERY_TEST_INFO, {"id": qid}, rx)
    if err:
        return None, None, None, err
    if not (data2.get("success") and data2.get("data")):
        return None, None, None, data2.get("message") or "获取题目失败"
    d = data2["data"]
    questions = d.get("question") or []
    if not questions:
        return None, None, None, "题库为空"

    period = parsed.get("activeMonths") or parsed.get("activeId") or parsed.get("id") or "-"
    meta = {
        "testName": d.get("testName") or TEMPLATE_NAME.get(template),
        "activeMonths": period,
        "totalScore": d.get("totalScore"),
        "passGrade": d.get("passGrade"),
        "testDuration": d.get("testDuration"),
    }
    name = (d.get("testName") or TEMPLATE_NAME.get(template)) + period
    return meta, questions, name, None


def build_markdown(meta, questions):
    """根据解析结果生成 Markdown 文本。"""
    type_count = {}
    for q in questions:
        t = TYPE_NAME.get(q.get("questionType"), "题型" + str(q.get("questionType")))
        type_count[t] = type_count.get(t, 0) + 1
    count_desc = "  ".join(f"{k} {v}题" for k, v in type_count.items())

    lines = []
    lines.append(f"# {meta.get('testName', '题库')} 题库")
    lines.append("")
    lines.append(f"- 月份：{meta.get('activeMonths', '-')}")
    lines.append(f"- 题量：{len(questions)} 题（{count_desc}）")
    if meta.get("totalScore"):
        lines.append(f"- 总分：{meta.get('totalScore')} 分"
                     + (f" ｜ 及格：{meta.get('passGrade')} 分" if meta.get("passGrade") else ""))
    if meta.get("testDuration"):
        lines.append(f"- 考试时长：{meta.get('testDuration')} 分钟")
    lines.append("")

    for idx, q in enumerate(questions, 1):
        qtype = TYPE_NAME.get(q.get("questionType"), "题型" + str(q.get("questionType")))
        lines.append(f"## {idx}. 【{qtype}】")
        lines.append("")
        lines.append(q.get("questionName", "").strip())
        lines.append("")
        for o in q.get("quesOption", []):
            mark = " ✓" if o.get("isTrue") == "1" else ""
            lines.append(f"- {o.get('optionNum')}. {o.get('optionContent', '').strip()}{mark}")
        lines.append("")
        ans_pairs = [f"{o.get('optionNum','')}.{o.get('optionContent','').strip()}"
                     for o in q.get("quesOption", []) if o.get("isTrue") == "1"]
        if ans_pairs:
            lines.append(f"**答案：{'；'.join(ans_pairs)}**")
        explain = q.get("questionExplain", "").strip()
        if explain:
            lines.append(f"**解析：** {explain}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def build_text(meta, questions):
    """生成纯文本（.txt）格式，避免 Markdown 语法符号。"""
    type_count = {}
    for q in questions:
        t = TYPE_NAME.get(q.get("questionType"), "题型" + str(q.get("questionType")))
        type_count[t] = type_count.get(t, 0) + 1
    count_desc = "  ".join(f"{k} {v}题" for k, v in type_count.items())

    lines = []
    lines.append(f"{meta.get('testName', '题库')} 题库")
    lines.append("")
    lines.append(f"月份：{meta.get('activeMonths', '-')}")
    lines.append(f"题量：{len(questions)} 题（{count_desc}）")
    if meta.get("totalScore"):
        line = f"总分：{meta.get('totalScore')} 分"
        if meta.get("passGrade"):
            line += f" ｜ 及格：{meta.get('passGrade')} 分"
        lines.append(line)
    if meta.get("testDuration"):
        lines.append(f"考试时长：{meta.get('testDuration')} 分钟")
    lines.append("")

    for idx, q in enumerate(questions, 1):
        qtype = TYPE_NAME.get(q.get("questionType"), "题型" + str(q.get("questionType")))
        lines.append("=" * 48)
        lines.append(f"{idx}. 【{qtype}】")
        lines.append("")
        lines.append(q.get("questionName", "").strip())
        lines.append("")
        for o in q.get("quesOption", []):
            lines.append(f"{o.get('optionNum')}. {o.get('optionContent', '').strip()}")
        lines.append("")
        ans_pairs = [f"{o.get('optionNum','')}.{o.get('optionContent','').strip()}"
                     for o in q.get("quesOption", []) if o.get("isTrue") == "1"]
        if ans_pairs:
            lines.append(f"答案：{'；'.join(ans_pairs)}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="党建云题目提取工具（月月学/项目学习/学习用典）")
    parser.add_argument("url", nargs="?", help="浏览器里的完整网址")
    parser.add_argument("--url", dest="url_opt", help="完整网址（等价于位置参数）")
    parser.add_argument("-o", "--out", help="输出文件路径（.md 或 .txt；不指定则按格式自动命名）")
    parser.add_argument("--md", action="store_true", help="导出 Markdown(.md)（默认纯文本 .txt）")
    args = parser.parse_args()

    url = args.url or args.url_opt
    if not url:
        parser.error('请提供完整网址，例如：python cnpc_extract.py "https://m.dj.cnpc.com.cn/.../detailedInfo.html?...&activeMonths=202608"')

    parsed = parse_url(url)
    print("解析结果：")
    print(f"  域名    = {parsed['origin']}")
    print(f"  模板    = {parsed['template']}（{TEMPLATE_NAME.get(parsed['template'], '?')}）")
    print(f"  rx_token= {parsed['rx_token']}")

    meta, questions, name, err = extract(parsed)
    if err:
        print(f"✗ {err}")
        sys.exit(1)
    print(f"✓ 成功提取 {len(questions)} 道题（{name}）")

    use_txt = not args.md  # 默认纯文本
    content = build_text(meta, questions) if use_txt else build_markdown(meta, questions)
    fmt_name = "纯文本(.txt)" if use_txt else "Markdown(.md)"

    print("\n" + "=" * 60)
    print(content)
    print("=" * 60)

    out_path = args.out
    if not out_path:
        ext = ".txt" if use_txt else ".md"
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{name}_题库{ext}")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n✓ 已保存题库（{fmt_name}）到：{out_path}")
    except Exception as e:
        print(f"⚠ 保存文件失败：{e}")


if __name__ == "__main__":
    main()
