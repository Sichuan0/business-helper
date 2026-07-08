# alibaba 详情页爬虫

爬 alibaba.com 商品详情页的「核心行业属性 (key attributes)」--功率、效率、电池类型、原产地、品牌、认证等规格字段，本来是做光伏设备出口市场调研用的。

## 它能干什么

- 通过 CDP 连接一个**已经手动登录过的真实 Chrome**，复用登录态去访问详情页。阿里盾对详情页会强制登录，匿名爬不动，这是当时唯一可行的办法。
- 断点续爬：进度记在 `out/keyattr_progress.json`，中断后再跑会跳过已爬的。
- 中英文规格字段通吃，能从 `.module_attribute`、`dl/dt+dd`、`table tr` 多种 DOM 结构里抠字段；带一套兜底的关键词正则。

## 老实说，缺点很明显

- **慢**。每条商品间隔 5–9 秒，每爬 30 条还要歇 30 秒，命中风控时冷却 90 秒。1000 多条跑下来得好几个小时。
- **偶尔触发风控**。阿里云盾会弹滑块验证码，这时候脚本会卡住，**需要你切到那个 Chrome 窗口手动把滑块滑过去**，然后它才能继续。不是全自动的。
- **得先手动登录**。脚本本身不处理登录，你得自己开一个带调试端口的 Chrome、手动登 alibaba 账号、过了人机验证，脚本才能连上去。
- 依赖输入数据 `out/four_categories.json`（列表页爬出来的商品 URL 清单）。单独跑这个脚本、没有这份输入数据是跑不起来的。

## 怎么用

1. 关掉所有 Chrome，用调试端口启动一个新数据目录的 Chrome：

   ```
   "C:/Program Files/Google/Chrome/Application/chrome.exe" \
     --remote-debugging-port=9222 \
     --user-data-dir="C:/somewhere/chrome_login" \
     "https://login.alibaba.com"
   ```

   > 不能用默认 Chrome profile 开调试端口（Chrome 禁止），必须用新数据目录。

2. 在这个 Chrome 里手动登录 alibaba，过掉人机验证。
3. 准备好 `out/four_categories.json`（列表页爬取结果，格式是 `{品类: [{url, ...}, ...]}`）。
4. `python crawl_keyattrs.py`，开始爬。遇到滑块就切过去手动滑。

## 依赖

```
pip install playwright
playwright install chromium
```

## 适用场景

个人市场调研、小批量规格采集。**不适合大规模商业抓取**--速率卡得很死，风控一上来就得人工介入，本来就是为「慢慢爬、爬够用就行」设计的。
