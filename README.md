# trade-doc

用 Claude Code Skill + Python 脚本，把非结构化输入（询盘 / 信用证 / 口述）变成外贸单证 docx。

---

## ⚠️ 这是什么、不是什么

**非常不成熟，个人玩具项目。** 没有界面、没有后端、单证类型很少、没经过任何生产验证，代码量也小。

市面上已经有**成熟的商业产品**——各种外贸 AI 单证 SaaS，有完整 UI、后端、模板库、在线编辑器、邮件发送、多语言、HS 编码查询等等。**功能类似，但远比这个完整、可靠。**

这个项目唯一的不同：**免费、开源、可自己改。** 适合学习 / 练手 / 定制，不适合真的拿去做生意。如果你是外贸从业者要日常出单，请直接用商业产品。

## 包含什么

### 1. Claude Code Skill (`skill/`) — 对话式生成形式发票

把 `skill/` 复制到 `~/.claude/skills/trade-doc/`，重启 Claude Code，然后用自然语言对话：

> "做一份形式发票给 ABC 公司，卖方上海某某贸易，FOB 上海，USD，30% 预付 70% 发货前付清，产品是 widget 100 个单价 10 刀"

Claude 会：抽取字段 → 缺必填就追问 → 齐了写 JSON → 调 `render_doc.py` 生成 docx → 给你文件路径。

核心思路：**LLM 负责抽取与追问，脚本负责渲染。** 永远不让 LLM 直接生成 docx 二进制。

- 目前只实现了 `proforma_invoice`（形式发票）一种。
- 加新单证：在 `schemas/` 加一份 json + 在 `render_doc.py` 的 `RENDERERS` 加一个渲染函数。

### 2. `scripts/extract_lc_docs.py` — 拆分单证表格

把一份含多张单证表格的 docx（如教师答案 / 练习册）按表格索引拆成独立 docx，并做文本修正（HS 编码、笔误等）。针对单证考试练习册的格式写的。

```
python scripts/extract_lc_docs.py --src "答案.docx" --out-dir ./输出
```

## 安装与使用

```bash
pip install python-docx

# 装 skill
cp -r skill/ ~/.claude/skills/trade-doc/   # Windows: C:\Users\<你>\.claude\skills\trade-doc\
# 重启 Claude Code，然后对 Claude 说要做单证即可

# 直接跑渲染脚本（不经过对话）
python skill/scripts/render_doc.py --data examples/sample_pi_data.json --out PI.docx
```

## 依赖

- Python 3.10+
- `python-docx`（`pip install python-docx`）

## 已知局限

- 只支持形式发票（PI）一种单证类型。
- 没有提单、装箱单、保险单、汇票等的独立渲染器（`extract_lc_docs.py` 只是拆分已有表格，不是从数据生成）。
- 没有模板上传、在线编辑、邮件发送、多语言等任何商业产品里的功能。
- 没有测试、没有错误恢复、没有并发——出错就报错退出。

## License

MIT
