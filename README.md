# 📊 Daily Market Pulse · 每日美股情绪仪表盘

每天自动抓取美股核心情绪指标，生成专业的可视化仪表盘。打开网页就能看最新数据。

**指标涵盖：** 标普500、纳指100、VIX、VXN、RSI(14)、CNN Fear & Greed、黄金、10Y美债

---

## 🚀 部署指南（小白专用）

按下面步骤一步一步来，全程预计 15 分钟。

### 第 1 步：注册 GitHub 账号

1. 打开 https://github.com
2. 点右上角 **Sign up** 注册
3. 填邮箱、密码、用户名（用户名会出现在你的网址里，建议简短英文）
4. 验证邮箱

### 第 2 步：创建一个新仓库

1. 登录后点右上角 **+** → **New repository**
2. **Repository name** 填：`market-pulse`
3. 选 **Public**（必须公开，GitHub Pages 免费版要求）
4. **不要**勾选 "Add a README file"
5. 点 **Create repository**

### 第 3 步：上传所有文件

最简单的方法：**直接在网页上拖拽上传**。

1. 在新仓库页面，点 **uploading an existing file** 链接（或 Add file → Upload files）
2. 把这个项目的所有文件**全选拖到上传区**：
   - `index.html`
   - `scripts/fetch_data.py`
   - `.github/workflows/update-data.yml`
   - `README.md`（这个文件）
3. 滚到底部，点 **Commit changes**

⚠️ **注意：** 拖文件夹时，要保留目录结构。如果不会拖文件夹，可以一个个文件上传：
- 先上传 `index.html` 和 `README.md` 到根目录
- 然后点 "Add file" → "Create new file"，文件名输入 `scripts/fetch_data.py`（注意斜杠会自动建文件夹），把脚本内容粘进去
- 同样建 `.github/workflows/update-data.yml`

### 第 4 步：开启 GitHub Pages

1. 仓库页面顶部点 **Settings**
2. 左侧菜单点 **Pages**
3. **Source** 选 **Deploy from a branch**
4. **Branch** 选 **main**，文件夹选 **/ (root)**
5. 点 **Save**
6. 等 1 分钟，刷新这个页面，会看到一个网址：
   `https://你的用户名.github.io/market-pulse/`
7. **把这个网址加到手机/电脑书签** ✅

### 第 5 步：手动触发一次数据抓取

第一次需要手动跑一下，否则 data.json 不存在：

1. 仓库顶部点 **Actions**
2. 左侧点 **Update Market Data**
3. 右侧点 **Run workflow** → 再点绿色按钮 **Run workflow**
4. 等 1-2 分钟，看到绿色 ✅ 就是成功了
5. 现在打开你的网址，应该能看到完整的仪表盘 🎉

---

## 📅 自动更新时间

设置好之后，**每个交易日**自动抓取 4 次（北京时间）：
- 21:30 - 美股开盘
- 01:00 - 午盘
- 04:05 - 收盘后
- 07:00 - 晚间确认

每天还会运行一次（含周末），保持周末 F&G 历史数据更新。

---

## 🔧 常见问题

**Q：网页显示"数据加载失败"？**  
A：去 Actions 标签页手动跑一次 workflow（第 5 步操作）。

**Q：数据多久更新一次？**  
A：交易日每天 4 次，每次抓完数据自动 commit 到仓库，触发 GitHub Pages 重新发布，大约 30 秒后你打开就是新数据。

**Q：能不能加更多指标？**  
A：能。改 `scripts/fetch_data.py` 的 TICKERS 字典，加上你想要的代码（Yahoo Finance 格式）。

**Q：免费版 GitHub Actions 够用吗？**  
A：完全够。每次抓数据耗时 ~30 秒，每月用量约 60 分钟，免费额度是 2000 分钟/月。

**Q：能分享给别人看吗？**  
A：能。你的 GitHub Pages 网址是公开的，任何人打开都能看。

---

## 📁 文件结构

```
market-pulse/
├── index.html                          ← 仪表盘网页
├── data.json                           ← 自动生成的数据（首次跑后才有）
├── scripts/
│   └── fetch_data.py                   ← 数据抓取脚本
├── .github/
│   └── workflows/
│       └── update-data.yml             ← 自动化定时任务
└── README.md                           ← 本文档
```

---

## 🛠 本地测试（可选）

如果想在自己电脑上先跑一下试试：

```bash
pip install yfinance pandas requests numpy
python scripts/fetch_data.py
# 然后用浏览器打开 index.html
```

---

**仅供参考，非投资建议。**
