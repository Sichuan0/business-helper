# -*- coding: utf-8 -*-
"""批量爬 1056 条商品的 key attributes (CDP 连接已开 Chrome, 登录态).
- 断点续爬: out/keyattr_progress.json 记录 {url: kvs}
- 速率: 每条间隔 5-9s, 每爬 30 条歇 30s, 风控则冷却 90s
- 中英文通用提取
输出: out/keyattrs.json (url -> kvs), 再合并进 four_categories.json 导 Excel."""
import json, random, re, time, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

DATA = json.loads(Path("out/four_categories.json").read_text(encoding="utf-8"))
PROG = Path("out/keyattr_progress.json")
CDP = "http://localhost:9222"

# 加载进度
progress = json.loads(PROG.read_text(encoding="utf-8")) if PROG.exists() else {}
print(f"已有进度: {len(progress)} 条")

# 收集所有 url (去重, 保留品类)
all_urls = []
for cat, items in DATA.items():
    for it in items:
        u = it.get("url")
        if u and u not in progress:
            all_urls.append((cat, u, it))
print(f"待爬: {len(all_urls)} 条")

EXTRACT_JS = r"""
() => {
  const out = {len: document.body.innerText.length, url: location.href};
  const lower = document.body.innerText.toLowerCase();
  out.punished = document.body.innerText.includes("login.alibaba") || lower.includes("rgv587") || lower.includes("verify your") || (out.len < 800);
  const kvs = {};
  const containers = document.querySelectorAll('.module_attribute, .module_3_tab_key_attribute, [class*="module_attribute"], [class*="key_attribute"], [class*="do-entry-item"]');
  containers.forEach(c => {
    let pairs = c.querySelectorAll('.attr-name,.attr-value,[class*="attr-name"],[class*="attr-value"]');
    if (pairs.length >= 2 && pairs.length % 2 === 0) {
      for (let i=0; i<pairs.length; i+=2) {const n=(pairs[i].innerText||'').trim(), v=(pairs[i+1].innerText||'').trim(); if(n) kvs[n]=v;}
    }
    c.querySelectorAll('dl').forEach(dl=>{const dts=dl.querySelectorAll('dt'), dds=dl.querySelectorAll('dd'); dts.forEach((dt,i)=>{if(dds[i]) kvs[dt.innerText.trim()]=dds[i].innerText.trim();});});
    c.querySelectorAll('table tr').forEach(tr=>{const cells=tr.querySelectorAll('th,td'); if(cells.length>=2) kvs[cells[0].innerText.trim()]=cells[1].innerText.trim();});
    if (Object.keys(kvs).length < 2) {
      const txt = (c.innerText||'').replace(/\s+/g,' ').trim();
      const keys = ['Cell size','电池片尺寸','Type','类型','Panel Efficiency','组件效率','Efficiency','效率','Place of Origin','原产地','Brand Name','品牌','Brand','Model Number','型号','Model','Panel Dimensions','面板尺寸','Dimensions','Warranty','保修','Weight','重量','Cell Type','电池类型','Max Power','最大功率','Power Tolerance','功率公差','Junction Box','接线盒','Connector','连接器','Frame','边框','Glass','玻璃','Application','应用','Mounting Type','安装方式','Output Voltage','输出电压','Output Frequency','输出频率','Battery Type','电池类型','Battery Capacity','电池容量','Work Time','工作时间','Controller Type','控制器类型','Certificate','认证','证书','Max System Voltage','最大系统电压','Operate Temperature','工作温度','Load Power','负载功率','Pump Head','扬程','Head','Material','材质','Number of Cells','电池数量','Cell Arrangement','电池排列','Maximum Power','最大功率','Open Circuit Voltage','开路电压','Short Circuit Current','短路电流','Module Efficiency','组件效率','Operating Temperature','工作温度','Output Power','输出功率','Phase','相数','Display','显示','Communication','通讯','Protection','保护','Solar Panel Type','太阳能板类型','System Voltage','系统电压','System Type','系统类型','Grid Type','电网类型'];
      const found=[]; keys.forEach(k=>{const idx=txt.indexOf(k); if(idx>=0) found.push({k,idx});});
      found.sort((a,b)=>a.idx-b.idx);
      for(let i=0;i<found.length;i++){const valEnd=i+1<found.length?found[i+1].idx:txt.length; const val=txt.slice(found[i].idx+found[i].k.length, valEnd).trim(); if(val&&val.length<80) kvs[found[i].k]=val;}
    }
  });
  out.kvs = kvs;
  return out;
}
"""

def save():
    PROG.write_text(json.dumps(progress, ensure_ascii=False), encoding="utf-8")

count = 0
consecutive_block = 0
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp(CDP)
    ctx = b.contexts[0]
    page = ctx.new_page()
    for cat, url, it in all_urls:
        # 风控冷却
        if consecutive_block >= 3:
            print(f"  [连续3次风控, 冷却90s]"); time.sleep(90); consecutive_block = 0
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
            for _ in range(8):
                page.mouse.wheel(0, 800); page.wait_for_timeout(random.randint(350,650))
            page.wait_for_timeout(2000)
            info = page.evaluate(EXTRACT_JS)
            if info["punished"] or len(info["kvs"]) == 0:
                consecutive_block += 1
                print(f"  [BLOCK/punished] {cat} len={info['len']} kvs={len(info['kvs'])}")
                progress[url] = {"_blocked": True, "_cat": cat, "_len": info["len"]}
                # 重试一次
                if consecutive_block <= 2:
                    time.sleep(60); continue
            else:
                consecutive_block = 0
                progress[url] = info["kvs"]
                count += 1
                # 取关键字段预览
                kv = info["kvs"]
                eff = kv.get("Panel Efficiency") or kv.get("组件效率") or kv.get("Efficiency") or kv.get("效率") or ""
                brand = kv.get("Brand Name") or kv.get("品牌") or kv.get("Brand") or ""
                origin = kv.get("Place of Origin") or kv.get("原产地") or ""
                print(f"  [{count}] {cat[:8]} | kvs={len(kv)} | {brand}/{eff}/{origin[:20]}")
        except Exception as e:
            print(f"  [ERR] {str(e)[:70]}")
            progress[url] = {"_error": str(e)[:80], "_cat": cat}
        # 定期保存 + 速率
        if count % 10 == 0:
            save()
        # 每30条歇一会
        if count and count % 30 == 0:
            print(f"  [已爬{count}, 歇30s]"); time.sleep(30)
        time.sleep(random.uniform(5, 9))
    save()
    b.close()

print(f"\n[完成] 本次新增 {count} 条, 进度库共 {len(progress)} 条")
