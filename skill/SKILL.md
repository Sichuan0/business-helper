---
name: trade-doc
description: 外贸单证生成助手。把非结构化输入（询盘/邮件/口述/聊天记录）变成标准外贸单证 docx 文件——形式发票(PI)、商业发票(CI)、装箱单(PL)、报价单等。缺必填信息时会主动向用户追问补全，齐了后调用脚本生成 docx。当用户说"做一份 PI/形式发票/发票/装箱单/报价单"、"把这段询盘整理成单证"、"生成外贸单证"、"帮我把这些信息填成发票"等时使用。
---

# 外贸单证生成助手 (trade-doc)

把非结构化输入变成标准外贸单证 docx。核心原则：**LLM 负责抽取与追问，脚本负责渲染**。你（Claude）只产出一份完整的 JSON，docx 由 `scripts/render_doc.py` 确定性地生成——绝不自己手写 docx 二进制或让 LLM 直接产文件。

## 支持的单证类型
- `proforma_invoice` 形式发票 (PI) ← 默认
- （后续可加 commercial_invoice / packing_list / quotation，结构同理）

## 工作流程（每次必走）

### 1. 确定单证类型
听用户描述判断。无法判断就默认 `proforma_invoice` 并告知用户。

### 2. 加载 schema
读取本 skill 目录下 `schemas/<doc_type>.json`。这是你要填的"表"——`required` 必填、`optional` 选填、`auto` 自动计算、`fields` 每个字段的含义和示例。

### 3. 抽取 + 追问（核心环节）
从用户输入里尽可能多地填字段，然后：
- 列出**仍缺失的必填字段**（`required` 中的，含 `items` 里每条的 `item_required`）。
- 针对每个缺失必填，提一个**具体、聚焦**的问题；可一次问几个，但每条只问一件事并给示例提示。
- **选填字段不追问**，缺就缺，渲染时留"—"。
- 模糊信息（如"价格一百多""运费买家付"）要确认清楚再填。
- **可计算的不要问用户**（见 schema 的 `auto`）：
  - `items[].total_price` = quantity × unit_price
  - `total_amount` = 各行 total_price 之和
  - `pi_date` 未给则用今天日期
- `pi_number` 未给时，建议一个格式（如 `PI-2026-001`）并问用户确认，**不要静默生成**。
- 用户明确说"就这些，剩下留空/用默认"即可停止追问，进入渲染。

### 4. 渲染
所有必填齐了（或用户让用默认）后：
1. 把全部字段写成一份 **flat JSON**（顶层带 `doc_type`），保存到临时文件，如 `C:/Users/yh198/trade-doc-data.json`。
   - `items` 里 `quantity` / `unit_price` / `total_price` 用**数字类型**，不要字符串。
2. 运行渲染脚本（路径见下）：
   ```
   python "<skill目录>/scripts/render_doc.py" --data "<json路径>" --out "<输出docx路径>"
   ```
   - 脚本路径：`C:/Users/yh198/.claude/skills/trade-doc/scripts/render_doc.py`
   - 输出默认放用户当前工作目录，文件名用 `PI-<pi_number>.docx`。
3. 脚本会再校验一次必填；若缺会非零退出并列出——补齐 JSON 后重跑。
4. 成功后，把生成的 docx **绝对路径**告诉用户，并简述填了什么、哪些选填留空了、合计金额。

## 依赖
- `python-docx`（已装）。若运行报 `ModuleNotFoundError: No module named 'docx'`，先 `pip install python-docx` 再跑。
- Python 命令：直接用 `python`。

## 输出 JSON 示例（flat 结构）
```json
{
  "doc_type": "proforma_invoice",
  "pi_number": "PI-2026-001",
  "pi_date": "2026-07-07",
  "seller_name": "Shanghai ABC Trading Co., Ltd.",
  "seller_address": "123 Factory Road, Shanghai, China",
  "seller_contact": "Tel: +86-21-12345678",
  "buyer_name": "XYZ Import GmbH",
  "buyer_address": "456 Market St, Berlin, Germany",
  "incoterms": "FOB Shanghai",
  "currency": "USD",
  "payment_terms": "30% T/T in advance, 70% before shipment",
  "delivery_time": "30 days after order confirmation",
  "validity": "30 days",
  "origin": "China",
  "shipping_method": "By sea",
  "items": [
    {"description": "Stainless Steel Widget, Model X1", "hs_code": "73269090", "quantity": 100, "unit": "PCS", "unit_price": 10.0, "total_price": 1000.0},
    {"description": "Widget Accessory Kit", "quantity": 50, "unit": "SET", "unit_price": 20.0, "total_price": 1000.0}
  ],
  "total_amount": 2000.0
}
```

## 注意
- 金额：`currency` 是币种代码（USD/CNY/EUR…），渲染时金额前会带币种。
- 中英文：单证内容用用户给的原文语言；模板标题/表头固定英文（外贸惯例）。
- 不要把 docx 内容贴给用户看全文——告诉路径和摘要即可，让用户自己打开文件。
