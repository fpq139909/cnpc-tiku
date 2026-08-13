#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
党建云题目提取工具 —— 本地软件版（图形界面）

启动后自动打开浏览器，支持三种来源的提取：
  - 月月学      ：粘贴「练」后的完整网址
  - 项目学习    ：粘贴「练」后的完整网址
  - 学习用典    ：粘贴「练」后的完整网址
检测按钮可一键核对三处最新条目是否打钩；未打钩时自动把「练」地址填入对应框（平台完成打卡须先双击进入「学」、再双击进入「练」）。
导出为纯文本 .txt；仅监听本机 127.0.0.1，不上传任何数据。

用法：
  python cnpc_app.py
然后浏览器访问 http://127.0.0.1:8000
"""

import os
import sys
import json
import webbrowser
import http.server
import urllib.request
import urllib.error

# 复用命令行版的核心逻辑（解密 / API / 解析 / 格式化）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cnpc_extract as core

PORT = int(os.environ.get("PORT", 8000))

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>党建云 题目提取</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
         background: #f4f6f9; color: #1f2329; }
  .wrap { max-width: 860px; margin: 0 auto; padding: 24px 16px 60px; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  .sub { color: #8a9099; font-size: 13px; margin-bottom: 20px; }
  .card { background: #fff; border: 1px solid #e6e9ef; border-radius: 12px; padding: 18px;
          box-shadow: 0 2px 10px rgba(20,40,80,.04); margin-bottom: 18px; }
  label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
  textarea, input[type=text] { width: 100%; border: 1px solid #d7dce5; border-radius: 8px;
          padding: 10px 12px; font-size: 14px; font-family: inherit; outline: none; }
  textarea { height: 92px; resize: vertical; }
  textarea:focus, input:focus { border-color: #2f6fed; }
  .hint { font-size: 12px; color: #8a9099; margin: 8px 0 0; line-height: 1.6; }
  .hint code { background: #eef1f6; padding: 1px 5px; border-radius: 4px; font-size: 12px; }
  button.go { background: #2f6fed; color: #fff; border: none; border-radius: 8px;
          padding: 11px 26px; font-size: 15px; font-weight: 600; cursor: pointer; }
  button.go:disabled { background: #aab6d8; cursor: not-allowed; }
  button.ghost { background: #fff; color: #2f6fed; border: 1px solid #2f6fed; border-radius: 8px;
          padding: 9px 18px; font-size: 14px; cursor: pointer; margin-left: 8px; }
  .status { margin-top: 14px; font-size: 14px; min-height: 20px; }
  .err { color: #d93636; }
  .ok { color: #2a9d4a; }
  .meta { display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: 13px; color: #5a6472;
          margin-bottom: 14px; }
  .meta b { color: #1f2329; font-weight: 600; }
  .q { border: 1px solid #eef1f6; border-radius: 10px; padding: 14px 16px; margin-bottom: 14px;
       background: #fcfdff; }
  .q-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .badge { background: #eaf1ff; color: #2f6fed; font-size: 12px; font-weight: 700;
           padding: 2px 9px; border-radius: 20px; }
  .q-no { font-weight: 700; color: #8a9099; font-size: 14px; }
  .stem { font-size: 15px; line-height: 1.7; margin-bottom: 10px; white-space: pre-wrap; }
  .opts { list-style: none; padding: 0; margin: 0; }
  .opt { padding: 8px 10px; border-radius: 8px; margin-bottom: 6px; font-size: 14px;
         line-height: 1.6; display: flex; align-items: flex-start; gap: 8px;
         border: 1px solid #eef1f6; background: #fff; }
  .opt.correct { background: #eafaf0; border-color: #b6e8c6; }
  .opt .n { font-weight: 700; min-width: 18px; }
  .opt.correct .n { color: #1f9d4a; }
  .tag { margin-left: auto; font-size: 12px; color: #1f9d4a; font-weight: 700; }
  .answer { margin-top: 8px; font-size: 14px; }
  .answer b { color: #1f9d4a; }
  .explain { margin-top: 6px; font-size: 13px; color: #5a6472; line-height: 1.65;
             white-space: pre-wrap; }
  .explain b { color: #3a4250; }
  .actions { margin: 8px 0 4px; }
  hr.sep { border: none; border-top: 1px solid #eef1f6; }
  .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
  .tab { flex: 1; padding: 11px 0; font-size: 15px; font-weight: 600; cursor: pointer;
         border: 1px solid #d7dce5; border-radius: 10px; background: #fff; color: #5a6472; }
  .tab.active { background: #2f6fed; border-color: #2f6fed; color: #fff; }
  .panel { display: none; }
  .panel.active { display: block; }
  details.adv { margin-top: 12px; border: 1px solid #eef1f6; border-radius: 8px; padding: 4px 10px; }
  details.adv summary { cursor: pointer; font-size: 13px; color: #5a6472; padding: 4px 0; }
  details.adv[open] summary { color: #2f6fed; font-weight: 600; }
  details.adv label.chk { display: inline-flex; align-items: center; gap: 6px; font-weight: 400;
           font-size: 13px; color: #5a6472; margin-top: 6px; }
  input[type=month] { width: 100%; border: 1px solid #d7dce5; border-radius: 8px;
           padding: 10px 12px; font-size: 14px; font-family: inherit; outline: none; }
  /* 打钩状态检测 */
  .check-card h2 { font-size: 16px; margin: 0 0 4px; }
  .ck-row { display: flex; align-items: center; gap: 10px; padding: 10px 12px;
            border: 1px solid #eef1f6; border-radius: 10px; margin-bottom: 10px; background: #fcfdff; }
  .ck-name { font-weight: 700; min-width: 64px; }
  .ck-desc { flex: 1; color: #5a6472; font-size: 13px; }
  .ck-badge { font-size: 13px; font-weight: 700; padding: 4px 12px; border-radius: 20px; white-space: nowrap; }
  .ck-badge.ok { background: #eafaf0; color: #1f9d4a; border: 1px solid #b6e8c6; }
  .ck-badge.uncheck { background: #fdecec; color: #d93636; border: 1px solid #f3b7b7; }
  .ck-row.alert { border-color: #f3b7b7; background: #fff6f6; }
  .tab.alert { background: #fdecec; border-color: #f3b7b7; color: #d93636; }
  .field-gap { margin-top: 14px; }
  input.alert-border, textarea.alert-border { border-color: #f3b7b7 !important; background: #fff6f6; }
</style>
</head>
<body>
<div class="wrap">
  <h1>党建云 · 题目提取</h1>
  <div class="sub">本地软件 · 数据不上传 · 三个模块都粘贴完整网址（即「练」跳转后的地址；在平台完成打卡须先双击进入「学」、再双击进入「练」）；点「检测打钩状态」可核对最新条目是否打钩</div>

  <div class="card check-card">
    <h2>📋 打钩状态检测</h2>
    <div class="sub" style="margin-bottom:12px;">一键检测三处（月月学 / 项目学习 / 学习用典）最新条目的打钩情况；未打钩时会标红，并提示先双击进入「学」、再双击进入「练」，把地址填入对应框</div>
    <label for="check-token">rx_token（会话令牌，从浏览器地址栏 rx_token= 后复制）</label>
    <input type="text" id="check-token" placeholder="从浏览器地址栏 rx_token= 后复制那段 UUID 粘贴此处">
    <div style="margin-top:12px;">
      <button class="go" id="btn-check">🔍 检测打钩状态</button>
      <button class="go" id="btn-sync" style="background:#7a5cf0;margin-left:8px;">🔄 强制更新手机端题库</button>
    </div>
    <div class="status" id="check-status" style="margin-top:10px;"></div>
    <div id="check-result"></div>
  </div>

  <div class="card">
    <div class="tabs">
      <button class="tab active" data-tab="month">月月学</button>
      <button class="tab" data-tab="proj">项目学习</button>
      <button class="tab" data-tab="xxyd">学习用典</button>
    </div>

    <!-- 月月学：粘贴完整网址 -->
    <div class="panel active" id="panel-month">
      <label for="url-month">① 练 URL（月月学：先双击进入「学」、再双击进入「练」，复制「练」后地址）</label>
      <textarea id="url-month" placeholder="到月月学页面先双击进入「学」完成学习，再双击进入「练」，复制跳转后的完整网址，例如：&#10;https://mobilenew.xianfengdangjian.com.cn/.../oneMonthLearning/detailedInfo.html?rx_token=...&activeMonths=202608"></textarea>
      <p class="hint">填「练」后的地址：到月月学页面先双击进入「学」完成学习，再双击进入「练」，把跳转后的完整网址粘贴这里（自动填入时同理）。网址里的 <code>rx_token</code> 会自动使用。</p>
    </div>

    <!-- 项目学习：粘贴网址 -->
    <div class="panel" id="panel-proj">
      <label for="url-proj">① 练 URL（项目学习：先双击进入「学」、再双击进入「练」，复制「练」后地址）</label>
      <textarea id="url-proj" placeholder="到项目学习页面先双击进入「学」完成学习，再双击进入「练」，复制跳转后的完整网址，例如：&#10;https://mobilenew.xianfengdangjian.com.cn/.../projectLearning/detailedInfo.html?rx_token=...&activeId=...&id=..."></textarea>
      <p class="hint">填「练」后的地址：到对应网址先双击进入「学」完成学习，再双击进入「练」，把跳转后的完整网址粘贴这里。因参数无规律，需完整网址；网址里的 <code>rx_token</code> 会自动使用。</p>
    </div>

    <!-- 学习用典：粘贴网址 -->
    <div class="panel" id="panel-xxyd">
      <label for="url-xxyd">① 练 URL（学习用典：先双击进入「学」、再双击进入「练」，复制「练」后地址）</label>
      <textarea id="url-xxyd" placeholder="到学习用典页面先双击进入「学」完成学习，再双击进入「练」，复制跳转后的完整网址，例如：&#10;https://mobilenew.xianfengdangjian.com.cn/.../oneMonthLearningXxyd/detailedInfo.html?rx_token=...&activeId=..."></textarea>
      <p class="hint">填「练」后的地址：到对应网址先双击进入「学」完成学习，再双击进入「练」，把跳转后的完整网址粘贴这里。因参数无规律，需完整网址；网址里的 <code>rx_token</code> 会自动使用。</p>
    </div>

    <div class="row" style="margin-top:14px;">
      <button class="go" id="btn">提取题目</button>
    </div>
    <div class="status" id="status"></div>
  </div>

  <div id="result"></div>
</div>

<script>
const $ = (id) => document.getElementById(id);
let activeTab = 'month';

// 标签页切换
document.querySelectorAll('.tab').forEach(t => {
  t.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    $('panel-' + t.dataset.tab).classList.add('active');
    activeTab = t.dataset.tab;
    $('status').textContent = ''; $('status').className = 'status';
  });
});

// 记住/回填 rx_token
window.addEventListener('load', () => {
  const saved = localStorage.getItem('rxToken');
  if(saved){ $('check-token').value = saved; }
});

$('btn').addEventListener('click', async () => {
  let body;
  if(activeTab === 'month'){
    const url = $('url-month').value.trim();
    if(!url){ setStatus('请先粘贴月月学完整网址', 'err'); return; }
    body = { url };
  } else if(activeTab === 'proj'){
    const url = $('url-proj').value.trim();
    if(!url){ setStatus('请先粘贴项目学习完整网址', 'err'); return; }
    body = { url };
  } else if(activeTab === 'xxyd'){
    const url = $('url-xxyd').value.trim();
    if(!url){ setStatus('请先粘贴学习用典完整网址', 'err'); return; }
    body = { url };
  }

  setStatus('正在提取…', '');
  $('btn').disabled = true;
  try {
    const resp = await fetch('/api/extract', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body)
    });
    const data = await resp.json();
    if(!data.ok){ setStatus('✗ ' + data.error, 'err'); $('result').innerHTML=''; return; }
    setStatus('✓ 成功提取 ' + data.questions.length + ' 道题（' + data.meta.testName + '）', 'ok');
    render(data);
    download(data.name + '_题库.txt', data.txt, 'text/plain');
  } catch(e){
    setStatus('✗ 请求失败：' + e.message, 'err');
  } finally {
    $('btn').disabled = false;
  }
});

// 打钩状态检测
$('btn-check').addEventListener('click', async () => {
  let token = $('check-token').value.trim();
  if(!token){ token = localStorage.getItem('rxToken') || ''; }
  if(!token){ setCheck('请先填写 rx_token（从浏览器地址栏 rx_token= 后复制）', 'err'); return; }
  $('check-token').value = token;
  localStorage.setItem('rxToken', token);
  setCheck('正在检测…', '');
  $('btn-check').disabled = true;
  try {
    const resp = await fetch('/api/check', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ rxToken: token })
    });
    const data = await resp.json();
    if(!data.ok){ setCheck('✗ ' + data.error, 'err'); $('check-result').innerHTML=''; return; }
    renderCheck(data.checks);
  } catch(e){
    setCheck('✗ 请求失败：' + e.message, 'err');
  } finally {
    $('btn-check').disabled = false;
  }
});

function setCheck(msg, cls){ const s=$('check-status'); s.textContent=msg; s.className='status '+(cls||''); }

// 强制更新手机端题库（无视打钩状态，三科都同步一次；用于测试 / 补录 / 复习）
$('btn-sync').addEventListener('click', async () => {
  let token = $('check-token').value.trim();
  if(!token){ token = localStorage.getItem('rxToken') || ''; }
  if(!token){ setCheck('请先填写 rx_token（从浏览器地址栏 rx_token= 后复制）', 'err'); return; }
  $('check-token').value = token; localStorage.setItem('rxToken', token);
  setCheck('正在强制同步三科题库到手机端…', '');
  $('btn-sync').disabled = true;
  try {
    const resp = await fetch('/api/sync', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ rxToken: token })
    });
    const data = await resp.json();
    if(!data.ok){ setCheck('✗ ' + data.error, 'err'); return; }
    const map = { month:'月月学', proj:'项目学习', xxyd:'学习用典' };
    const parts = ['month','proj','xxyd'].map(k=>{
      const r = data.sync[k];
      return map[k] + (r && r.ok ? ' ✓已同步' : ' ✗' + (r ? (r.error||'') : ''));
    });
    setCheck('强制同步完成：' + parts.join('；') + '（手机端刷新即可看到最新内容）', 'ok');
  } catch(e){
    setCheck('✗ 请求失败：' + e.message, 'err');
  } finally {
    $('btn-sync').disabled = false;
  }
});

function renderCheck(checks){
  const map = { month:'月月学', proj:'项目学习', xxyd:'学习用典' };
  const pos = { month:'最首', proj:'最顶部', xxyd:'最首' };
  const urlBox = { month:'url-month', proj:'url-proj', xxyd:'url-xxyd' };
  // 先清理上次的标红
  ['url-month','url-proj','url-xxyd'].forEach(id=>{ const b=$(id); if(b) b.classList.remove('alert-border'); });
  let anyUncheck=false, html='', filled=[], synced=[], pushErrs=[];
  ['month','proj','xxyd'].forEach(k=>{
    const c=checks[k], ok=c.checked;
    if(!ok){
      anyUncheck=true;
      // 未打钩：自动把「练」地址转录进对应 URL 框
      const box=$(urlBox[k]);
      if(box && c.practiceUrl){ box.value=c.practiceUrl; box.classList.add('alert-border'); filled.push(map[k]); }
      if(c.pushed) synced.push(map[k]);
      if(c.pushError) pushErrs.push(map[k] + '（' + c.pushError + '）');
    }
    const badge = ok ? '<span class="ck-badge ok">✓ 已打钩</span>'
                     : '<span class="ck-badge uncheck">✗ 未打钩</span>';
    html += '<div class="ck-row'+(ok?'':' alert')+'">'
          + '<span class="ck-name">'+map[k]+'</span>'
          + '<span class="ck-desc">'+pos[k]+'：'+esc(c.label)+'</span>'+badge+'</div>';
  });
  $('check-result').innerHTML = html;
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('alert'));
  if(anyUncheck){
    const tabs=[];
    if(!checks.month.checked) tabs.push('month');
    if(!checks.proj.checked) tabs.push('proj');
    if(!checks.xxyd.checked) tabs.push('xxyd');
    tabs.forEach(k=>{ const t=document.querySelector('.tab[data-tab="'+k+'"]'); if(t) t.classList.add('alert'); });
    if(tabs.length){ switchTab(tabs[0]); }
    let extra = '';
    if(synced.length) extra += '「' + synced.join('、') + '」题库已自动同步到手机端链接（检测后即时生效，无需重部署）。';
    if(pushErrs.length) extra += ' 手机端同步失败：' + pushErrs.join('；');
    if(filled.length){
      setCheck('⚠ '+filled.join('、')+' 未打钩：已自动把「练」地址填入下方对应框（标红），可直接点「提取题目」。'+extra+'提醒：在平台真正完成打卡须先双击进入「学」、再双击进入「练」。', 'err');
    } else {
      setCheck('⚠ '+tabs.map(k=>map[k]).join('、')+' 未打钩：请先到该网址双击进入「学」完成学习，再双击进入「练」，把「练」后的地址粘贴到下方对应框。'+extra, 'err');
    }
  } else {
    setCheck('✓ 三处最新条目均已打钩。', 'ok');
  }
}

function switchTab(tab){
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  const t=document.querySelector('.tab[data-tab="'+tab+'"]'); if(t) t.classList.add('active');
  const p=$('panel-'+tab); if(p) p.classList.add('active');
  activeTab=tab;
}

function setStatus(msg, cls){ $('status').textContent = msg; $('status').className = 'status ' + cls; }

function render(data){
  const r = $('result');
  const m = data.meta;
  const counts = (m.counts||[]).join('  ');
  let html = '<div class="card">'
    + '<div class="meta">'
    + '<span><b>标题：</b>' + esc(m.testName) + '</span>'
    + '<span><b>期间：</b>' + esc(m.activeMonths) + '</span>'
    + '<span><b>题量：</b>' + data.questions.length + ' 题（' + esc(counts) + '）</span>'
    + (m.totalScore ? '<span><b>总分：</b>' + esc(m.totalScore) + ' 分</span>' : '')
    + '</div><hr class="sep">';

  data.questions.forEach((q,i)=>{
    html += '<div class="q"><div class="q-head"><span class="badge">'+esc(q.typeName)
          + '</span><span class="q-no">第 '+(i+1)+' 题</span></div>'
          + '<div class="stem">'+esc(q.name)+'</div><ul class="opts">';
    const ansText = q.options.filter(o => o.isTrue)
      .map(o => o.num + '.' + o.content).join('；');
    q.options.forEach(o=>{
      const c = o.isTrue ? ' correct':'';
      html += '<li class="opt'+c+'"><span class="n">'+esc(o.num)+'.</span><span>'+esc(o.content)+'</span></li>';
    });
    html += '</ul><div class="answer">答案：<b>'+esc(ansText)+'</b></div>';
    html += '</div>';
  });
  html += '</div><div class="actions">'
    + '<button class="ghost" id="dl-txt">下载 .txt</button>'
    + '</div><hr class="sep">';

  r.innerHTML = html;

  $('dl-txt').onclick = () => download(data.name+'_题库.txt', data.txt, 'text/plain');
}

function download(filename, text, mime){
  const blob = new Blob([text], {type: mime+';charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = filename; a.click();
  URL.revokeObjectURL(a.href);
}
function esc(s){ return String(s==null?'':s).replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
</script>
</body>
</html>"""


def run_extraction(url):
    """执行提取（网址模式），返回 (payload_dict, error_msg)。"""
    if not url or not url.strip():
        return None, "请粘贴完整的网址"
    parsed = core.parse_url(url.strip())
    meta, questions, name, err = core.extract(parsed)
    if err:
        return None, err
    return build_payload(meta, questions, name), None


def build_payload(meta, questions, name):
    qlist = []
    type_count = {}
    for q in questions:
        tname = core.TYPE_NAME.get(q.get("questionType"), "题型" + str(q.get("questionType")))
        type_count[tname] = type_count.get(tname, 0) + 1
        opts = [{"num": o.get("optionNum"),
                 "content": o.get("optionContent", ""),
                 "isTrue": o.get("isTrue") == "1"}
                for o in q.get("quesOption", [])]
        qlist.append({
            "typeName": tname,
            "name": q.get("questionName", "").strip(),
            "options": opts,
            "answer": [o["num"] for o in opts if o["isTrue"]],
            "explain": q.get("questionExplain", "").strip(),
        })
    meta2 = dict(meta)
    meta2["counts"] = [f"{k} {v}题" for k, v in type_count.items()]
    meta2["randomNumber"] = core.now_beijing()
    return {
        "ok": True,
        "meta": meta2,
        "questions": qlist,
        "md": core.build_markdown(meta, questions),
        "txt": core.build_text(meta, questions),
        "name": name,
    }


# ---------- GitHub 仓库自动同步（手机端题库内容源，零干预） ----------
# 同步目标：公开仓库 fpq139909/cnpc-tiku 的 tiku/ 子目录；手机端经 jsDelivr CDN 读取
#   （jsDelivr 国内可达、CORS 全开，故检测后手机端自动变，无需重部署）
# 配置（与 cnpc_app.py 同目录）：
#   gist_token.txt : GitHub Personal Access Token（需 repo 或 public_repo 权限）
#   gh_repo.txt    : 两行 => "owner/repo" 与 "branch"（首次自动创建 cnpc-tiku 后写入）
GH_FILES = {"month": "yyx.txt", "proj": "xmxx.txt", "xxyd": "xxyd.txt"}
GH_SUBDIR = "tiku"


def load_gh_cfg():
    base = os.path.dirname(os.path.abspath(__file__))
    tok, owner, repo, branch = "", "", "", ""
    # 优先环境变量（云端部署填 GITHUB_TOKEN，避免把 token 写进公开仓库）
    tok = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if not tok:
        try:
            with open(os.path.join(base, "gist_token.txt"), encoding="utf-8") as f:
                tok = f.read().strip()
        except Exception:
            pass
    try:
        with open(os.path.join(base, "gh_repo.txt"), encoding="utf-8") as f:
            lines = [l.strip() for l in f.read().splitlines() if l.strip()]
        if lines:
            owner, repo = lines[0].split("/")
            branch = lines[1] if len(lines) > 1 else "main"
    except Exception:
        pass
    return tok, owner, repo, branch


def save_gh_repo(owner, repo, branch):
    base = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(base, "gh_repo.txt"), "w", encoding="utf-8") as f:
            f.write("%s/%s\n%s\n" % (owner, repo, branch))
    except Exception:
        pass


def _gh_api(method, url, token, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "token " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "cnpc-tool")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _gh_ensure_repo(tok):
    """确保同步仓库存在，返回 (owner, repo, branch) 或 (None, None, None)。"""
    try:
        me = _gh_api("GET", "https://api.github.com/user", tok)
        owner = me.get("login")
        repo = "cnpc-tiku"
        _, o, r2, b = load_gh_cfg()
        if o and r2:
            return o, r2, b or "main"
        try:
            d = _gh_api("GET", "https://api.github.com/repos/%s/%s" % (owner, repo), tok)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                d = _gh_api("POST", "https://api.github.com/user/repos", tok,
                            {"name": repo, "private": False, "auto_init": True,
                             "description": "党建云题库自动同步"})
            else:
                raise
        branch = d.get("default_branch") or "main"
        save_gh_repo(owner, repo, branch)
        return owner, repo, branch
    except Exception as e:
        print("ensure_repo err:", e)
        return None, None, None


def _gh_push_file(tok, owner, repo, branch, path, text, msg):
    api = "https://api.github.com/repos/%s/%s/contents/%s" % (owner, repo, path)
    sha = None
    try:
        req = urllib.request.Request(api + "?ref=" + branch,
            headers={"Authorization": "token " + tok, "Accept": "application/vnd.github+json",
                     "User-Agent": "cnpc"})
        with urllib.request.urlopen(req, timeout=30) as r:
            sha = json.loads(r.read().decode()).get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            return False, "读取失败 %d" % e.code
    except Exception:
        pass
    import base64
    body = {"message": msg, "content": base64.b64encode(text.encode("utf-8")).decode(),
            "branch": branch}
    if sha:
        body["sha"] = sha
    try:
        req = urllib.request.Request(api, data=json.dumps(body).encode(), method="PUT",
            headers={"Authorization": "token " + tok, "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json", "User-Agent": "cnpc"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, "HTTP %d" % r.status
    except urllib.error.HTTPError as e:
        return False, "GitHub %d" % e.code


def _jsdelivr_purge(owner, repo, branch, path):
    url = "https://purge.jsdelivr.net/"
    body = json.dumps({"path": ["/gh/%s/%s@%s/%s" % (owner, repo, branch, path)]}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=body, method="POST",
                                     headers={"Content-Type": "application/json", "User-Agent": "cnpc"})
        with urllib.request.urlopen(req, timeout=20) as r:
            # purge 接口成功返回 202 Accepted（不是 200），两者都算成功
            return r.status in (200, 202)
    except Exception:
        return False


def push_subject_txt(subject_key, text):
    """把题库纯文本同步到手机端：①写本地「题库手机版」(兜底) ②推送到 GitHub 仓库(经 jsDelivr 手机可读)。
    返回 (auto_ok, msg)：auto_ok 表示是否成功走通「自动通道」(GitHub+jsDelivr)，从而实现检测后手机端自动变。"""
    fname = GH_FILES.get(subject_key)
    if not fname:
        return False, "未知科目：" + str(subject_key)
    # ① 本地兜底
    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [os.path.join(base, "题库手机版"),
                  os.path.join(os.path.dirname(base), "题库手机版")]
    mob = next((c for c in candidates if os.path.isdir(c)), None) or candidates[1]
    try:
        os.makedirs(mob, exist_ok=True)
        with open(os.path.join(mob, fname), "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        return False, "写入本地题库失败：" + str(e)
    # ② 自动通道（GitHub 仓库 + jsDelivr）
    tok, owner, repo, branch = load_gh_cfg()
    if not tok:
        return False, "已更新本地题库（%s）；自动同步待配置 GitHub Token（需 repo 权限）" % fname
    if not owner:
        owner, repo, branch = _gh_ensure_repo(tok)
    if not owner:
        return False, "已更新本地题库（%s）；GitHub 仓库创建失败（请检查 Token 权限）" % fname
    ok, msg = _gh_push_file(tok, owner, repo, branch, "%s/%s" % (GH_SUBDIR, fname), text,
                           "sync %s" % fname)
    if ok:
        _jsdelivr_purge(owner, repo, branch, "%s/%s" % (GH_SUBDIR, fname))
        return True, "已自动同步到手机端（%s）" % fname
    return False, "已更新本地题库（%s）；GitHub 推送失败：%s" % (fname, msg)


def check_status(rx_token):
    """检测三处「最首」条目的打钩情况，返回每处 {label, checked, practiceUrl} 或 (None, 错误信息)。

    practiceUrl 为该条目「练」按钮跳转后的完整地址，供前端在未打钩时自动填入对应 URL 框。
    """
    if not rx_token:
        return None, "请填写会话令牌（rx_token）"
    tok = rx_token
    out = {}
    # 月月学：列表最首（最新）年月
    try:
        d, err = core.call_api("https://mobilenew.xianfengdangjian.com.cn",
            "/party/homePage/learningEachMonth/getFinishStatus", {"type": "0"}, tok)
        if err:
            return None, "月月学检测失败：" + err
        obj = d["data"]["obj"]
        first = obj[0]
        y = first.get("year") or ""
        m = str(first.get("month") or "0").zfill(2)
        am = "%s%s" % (y, m)
        out["month"] = {
            "label": "%s年%s月" % (y, int(first.get("month") or 0)),
            "checked": str(first.get("finished")) == "1",
            "practiceUrl": "https://mobilenew.xianfengdangjian.com.cn"
                           "/sydj-mobile/webcontent/template/oneMonthLearning/detailedInfo.html"
                           "?rx_token=%s&activeMonths=%s" % (tok, am),
        }
    except Exception as e:
        return None, "月月学检测异常：" + str(e)
    # 项目学习：列表最顶部活动
    try:
        d, err = core.call_api("https://mobilenew.xianfengdangjian.com.cn",
            "/party/homePage/safetyMonth/getFinishStatus", {}, tok)
        if err:
            return None, "项目学习检测失败：" + err
        obj = d["data"]["obj"]
        first = obj[0]
        aid = first.get("id") or ""   # = selectRegulation[0].id，也是「练」URL 的 activeId
        # 「练」URL 里的 id 来自页面主接口 getTotalCounts 返回的 selectRegulation[0].linkId
        # （与 getFinishStatus 的 id 不是同一个值，之前用错导致地址无效）
        link_id = aid
        try:
            tc, e2 = core.call_api("https://mobilenew.xianfengdangjian.com.cn",
                "/party/homePage/safetyMonth/getTotalCounts", {"activeId": aid}, tok)
            if not e2 and tc.get("data") and tc["data"].get("selectRegulation"):
                link_id = tc["data"]["selectRegulation"][0].get("linkId") or aid
        except Exception:
            pass
        out["proj"] = {
            "label": first.get("activeTitle") or "",
            "checked": str(first.get("finished")) == "1",
            "practiceUrl": "https://mobilenew.xianfengdangjian.com.cn"
                           "/sydj-mobile/webcontent/template/projectLearning/detailedInfo.html"
                           "?rx_token=%s&activeId=%s&id=%s" % (tok, aid, link_id),
        }
    except Exception as e:
        return None, "项目学习检测异常：" + str(e)
    # 学习用典：列表最首（最新）期数
    try:
        d, err = core.call_api("https://m.dj.cnpc.com.cn",
            "/party/homePage/learningEachMonthXxyd/getFinishStatus", {"type": "0"}, tok)
        if err:
            return None, "学习用典检测失败：" + err
        obj = d["data"]["obj"]
        first = obj[0]
        aid = first.get("activeId") or ""
        out["xxyd"] = {
            "label": first.get("month") or "",
            "checked": str(first.get("finished")) == "1",
            "practiceUrl": "https://m.dj.cnpc.com.cn"
                           "/sydj-mobile/webcontent/template/oneMonthLearningXxyd/detailedInfo.html"
                           "?rx_token=%s&activeId=%s" % (tok, aid),
        }
    except Exception as e:
        return None, "学习用典检测异常：" + str(e)
    # 未打钩科目：自动提取题库并写入本地「题库手机版」目录（供重新部署后手机端读取）
    pushed_any = []
    for k in ("month", "proj", "xxyd"):
        if not out[k]["checked"]:
            try:
                payload, e2 = run_extraction(out[k]["practiceUrl"])
                if e2:
                    out[k]["pushError"] = "提取失败：" + e2
                else:
                    ok2, msg2 = push_subject_txt(k, payload["txt"])
                    out[k]["pushed"] = ok2
                    if ok2:
                        pushed_any.append(k)
                    if not ok2:
                        out[k]["pushError"] = msg2
            except Exception as ex:
                out[k]["pushError"] = "同步异常：" + str(ex)
    return out, None


def build_practice_urls(rx_token):
    """构造三科「练」地址（无论是否打钩），供强制同步使用。返回 {month/proj/xxyd: url}。"""
    tok = rx_token
    urls = {}
    try:
        d, err = core.call_api("https://mobilenew.xianfengdangjian.com.cn",
            "/party/homePage/learningEachMonth/getFinishStatus", {"type": "0"}, tok)
        if not err:
            o = d["data"]["obj"][0]
            y = o.get("year") or ""; m = str(o.get("month") or "0").zfill(2)
            am = "%s%s" % (y, m)
            urls["month"] = ("https://mobilenew.xianfengdangjian.com.cn"
                "/sydj-mobile/webcontent/template/oneMonthLearning/detailedInfo.html"
                "?rx_token=%s&activeMonths=%s" % (tok, am))
    except Exception:
        pass
    try:
        d, err = core.call_api("https://mobilenew.xianfengdangjian.com.cn",
            "/party/homePage/safetyMonth/getFinishStatus", {}, tok)
        if not err:
            o = d["data"]["obj"][0]; aid = o.get("id") or ""
            link_id = aid
            try:
                tc, e2 = core.call_api("https://mobilenew.xianfengdangjian.com.cn",
                    "/party/homePage/safetyMonth/getTotalCounts", {"activeId": aid}, tok)
                if not e2 and tc.get("data") and tc["data"].get("selectRegulation"):
                    link_id = tc["data"]["selectRegulation"][0].get("linkId") or aid
            except Exception:
                pass
            urls["proj"] = ("https://mobilenew.xianfengdangjian.com.cn"
                "/sydj-mobile/webcontent/template/projectLearning/detailedInfo.html"
                "?rx_token=%s&activeId=%s&id=%s" % (tok, aid, link_id))
    except Exception:
        pass
    try:
        d, err = core.call_api("https://m.dj.cnpc.com.cn",
            "/party/homePage/learningEachMonthXxyd/getFinishStatus", {"type": "0"}, tok)
        if not err:
            o = d["data"]["obj"][0]; aid = o.get("activeId") or ""
            urls["xxyd"] = ("https://m.dj.cnpc.com.cn"
                "/sydj-mobile/webcontent/template/oneMonthLearningXxyd/detailedInfo.html"
                "?rx_token=%s&activeId=%s" % (tok, aid))
    except Exception:
        pass
    return urls


def force_sync_all(rx_token):
    """无视打钩状态，强制把三科题库同步到手机端（用于测试 / 补录 / 复习）。"""
    if not rx_token:
        return None, "请填写会话令牌（rx_token）"
    urls = build_practice_urls(rx_token)
    res = {}
    pushed_any = []
    for k in ("month", "proj", "xxyd"):
        if k not in urls:
            res[k] = {"ok": False, "error": "无法获取该科「练」地址（检测接口失败）"}
            continue
        try:
            payload, e2 = run_extraction(urls[k])
            if e2:
                res[k] = {"ok": False, "error": "提取失败：" + e2}
            else:
                ok2, msg2 = push_subject_txt(k, payload["txt"])
                res[k] = {"ok": ok2, "msg": msg2}
                if ok2:
                    pushed_any.append(k)
        except Exception as ex:
            res[k] = {"ok": False, "error": "同步异常：" + str(ex)}
    return res, None


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, ctype, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._send(404, "text/plain; charset=utf-8", "Not Found")
            return
        if self.path.startswith("/favicon"):
            self._send(204, "text/plain", b"")
            return
        self._send(200, "text/html; charset=utf-8", HTML)

    def do_POST(self):
        if self.path == "/api/extract":
            self.handle_extract()
        elif self.path == "/api/check":
            self.handle_check()
        elif self.path == "/api/sync":
            self.handle_sync()
        else:
            self._send(404, "application/json; charset=utf-8",
                       json.dumps({"ok": False, "error": "Not Found"}, ensure_ascii=False))

    def handle_extract(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            self._send(400, "application/json; charset=utf-8",
                       json.dumps({"ok": False, "error": "请求格式错误：" + str(e)}, ensure_ascii=False))
            return
        url = (body.get("url") or "").strip()
        if url:
            payload, err = run_extraction(url)
        else:
            err = "请粘贴完整的网址"
        if err:
            self._send(200, "application/json; charset=utf-8",
                       json.dumps({"ok": False, "error": err}, ensure_ascii=False))
            return
        self._send(200, "application/json; charset=utf-8",
                   json.dumps(payload, ensure_ascii=False))

    def handle_check(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            self._send(400, "application/json; charset=utf-8",
                       json.dumps({"ok": False, "error": "请求格式错误：" + str(e)}, ensure_ascii=False))
            return
        rx_token = (body.get("rxToken") or "").strip()
        res, err = check_status(rx_token)
        if err:
            self._send(200, "application/json; charset=utf-8",
                       json.dumps({"ok": False, "error": err}, ensure_ascii=False))
            return
        self._send(200, "application/json; charset=utf-8",
                   json.dumps({"ok": True, "checks": res}, ensure_ascii=False))

    def handle_sync(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            self._send(400, "application/json; charset=utf-8",
                       json.dumps({"ok": False, "error": "请求格式错误：" + str(e)}, ensure_ascii=False))
            return
        rx_token = (body.get("rxToken") or "").strip()
        res, err = force_sync_all(rx_token)
        if err:
            self._send(200, "application/json; charset=utf-8",
                       json.dumps({"ok": False, "error": err}, ensure_ascii=False))
            return
        self._send(200, "application/json; charset=utf-8",
                   json.dumps({"ok": True, "sync": res}, ensure_ascii=False))

    def log_message(self, *args):
        pass  # 静默


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    url = f"http://0.0.0.0:{PORT}/"
    print(f"党建云题目提取工具已启动：{url}")
    print("（此窗口保持打开；关闭窗口即停止服务）")
    # 云端环境不自动开浏览器；仅本地默认端口时尝试打开
    if PORT == 8000:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
