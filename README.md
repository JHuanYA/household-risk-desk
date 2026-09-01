# 家庭 / 个人财务风险监控台

**Household Financial Risk Desk** · PRD-HFRD-001

> **🚀 快速体验（推荐）**：双击打开 [`web/index.html`]([web/index.html](https://jhuanya.github.io/household-risk-desk/web/index.html)) 即可，无需安装任何环境、无需联网（Plotly.js 需首次联网加载）。
>
> 或启动 Streamlit 版（需要 Python）：`streamlit run app.py`

---

给个人或家庭用的流动性与偿付风险控制台：**看清家底 → 限制风险 → 在压力情景下判断会不会断现金流 → 给出可执行的处置建议**。

本仓库同时提供两种前端实现，共享同一套计算口径：

| 版本 | 技术栈 | 启动方式 | 适用场景 |
|---|---|---|---|
| **HTML 版（推荐）** | 纯 HTML + JS + Plotly.js CDN | 双击 `web/index.html` | 零安装、随时随地用、数据在浏览器本地 |
| **Streamlit 版** | Python 3.11+ + Streamlit + Plotly.py | `streamlit run app.py` | 需要读 CSV 文件、做批量数据分析 |

两者计算引擎逐行对齐，数值误差 < 1 HKD。

---

## 这是什么 / 不是什么

| ✅ 是 | ❌ 不是 |
|---|---|
| 家庭资产负债表 + 现金流 | 记账、预算信封、消费分类 |
| 流动性、杠杆、DSTI、集中度 | 个股 VaR、组合优化、荐股 |
| 可配置限额（绿 / 黄 / 红） | 银行审批、征信评分 |
| 压力测试与缺口建议 | 银行 API、PDF 账单识别 |

风险闭环固定为五步：**定义风险事件 → 计量现状 → 设定限额 → 压力测试 → 处置建议**。

两件被定义为「出事」：

1. **流动性断裂**：高流动性资产覆盖不了目标月数的必要支出（默认 6 个月）
2. **偿付危机**：净资产小于 0，或压力后净资产小于 0

---

## 功能一览

### HTML 版（6 页 SPA）

| 页面 | 路由 | 功能 |
|---|---|---|
| 🏠 总览 | `#dashboard` | 综合灯 + 5 指标卡 + 告警列表 + 资产饼图 + 压力预览 |
| 📝 数据输入 | `#data` | household 表 + cashflow 表 + FX 汇率，全部可前端编辑，改值即算 |
| 💰 资产负债 | `#balance` | 分类汇总 + 资产明细 + 负债明细 |
| 📊 现金流 | `#cashflow` | 收入/支出条形图 + 明细表 |
| ⚡ 压力测试 | `#stress` | 10 预置情景 + **6 个自定义滑块** + 对比表 + 击穿清单 + 失业辅助 |
| 📋 限额与假设 | `#limits` | 7 条限额状态 + 阈值说明 |

亮点功能：
- **输入校验**：金额负数、币种缺失、类别非法 → 红色横幅 + 行级高亮 + 阻断计算
- **自定义情景滑块**：收入/房产/投资/供款/负债/必要支出 6 个系数实时拖动重算
- **多币种**：HKD/USD/CNY 自动折算，汇率可前端编辑
- **零后端**：数据存 localStorage，刷新不丢

### Streamlit 版（5 页）

| 页面 | 对应文件 | 功能 |
|---|---|---|
| 总览 | `views/P0_总览.py` | 综合灯 + 指标 + 告警 + 饼图 + 失业辅助 |
| 资产负债表 | `views/P1_资产负债表.py` | 分类汇总 + 流动性分级 |
| 现金流 | `views/P2_现金流.py` | 收支结构 + 结余 |
| 压力测试 | `views/P3_压力测试.py` | 10 预置情景 + 击穿清单 |
| 限额与假设 | `views/P4_限额与假设.py` | 阈值 + 原因句 + 口径说明 |

---

## 快速开始

### 方式一：HTML 版（零门槛）

**不需要安装 Python、不需要 npm、不需要 server**。

```
直接双击打开 web/index.html
```

浏览器会提示 Plotly.js CDN 加载（约 2MB，首次需要联网）。数据全部在浏览器 localStorage 里，刷新不丢，换浏览器会重置。

### 方式二：Streamlit 版

需要 Python 3.11+。

```bash
# 1. 克隆
git clone <your-repo-url> household-risk-desk
cd household-risk-desk

# 2. 创建虚拟环境 + 安装依赖
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt

# 3. 启动
streamlit run app.py
```

浏览器打开 `http://localhost:8501` ，默认加载 `data/demo/` Demo 家庭。

---

## 仓库结构

```text
household-risk-desk/
├── README.md                     # 本文件
├── requirements.txt              # Streamlit 版依赖
├── app.py                        # Streamlit 入口
│
├── config/                       # ⚙️ 限额与情景配置
│   ├── limits.yaml               # 7 条风险限额（绿/黄/红阈值）
│   └── scenarios.yaml            # 10 个压力情景
│
├── data/                         # 📊 CSV 数据源（Streamlit 版用）
│   ├── household.csv             # 资产负债明细
│   ├── cashflow.csv              # 现金流明细
│   ├── fx.csv                    # 汇率表
│   ├── DEMO_CHECK.md             # 手工对账（数值精确到 1 HKD）
│   ├── demo/                     # 虚构 Demo 家庭（Git 可提交）
│   └── local/                    # 真实数据（.gitignore，禁止提交）
│
├── src/                          # 🧮 计算引擎（Streamlit 版）
│   ├── metrics.py                # 核心指标：净值/杠杆/DSTI/LIM/GAP 等
│   ├── limits.py                 # 7 条限额灯号判定
│   ├── scenarios.py              # 压力测试对比
│   ├── data_loader.py            # CSV 读取 + 汇率折算
│   └── theme.py                  # 深色主题配色
│
├── views/                        # 🖥️ Streamlit 页面
│   ├── P0_总览.py
│   ├── P1_资产负债表.py
│   ├── P2_现金流.py
│   ├── P3_压力测试.py
│   └── P4_限额与假设.py
│
└── web/                          # 🌐 HTML 版（纯前端 SPA）
    ├── index.html                # 入口 + 导航 + Plotly CDN
    ├── css/
    │   └── app.css               # 深色主题
    └── js/
        ├── engine.js             # 计算引擎（逐行对齐 src/）
        ├── state.js              # localStorage + 响应式状态管理
        ├── ui.js                 # 可编辑表格 + 格式化 + 输入校验
        ├── charts.js             # Plotly.js 封装
        ├── pages.js              # 6 页渲染 + hash 路由
        └── demo-data.js          # 历史备份（已合并入 engine.js）
```

**两套计算引擎口径 100% 对齐**：`src/*.py` 的每个公式在 `web/js/engine.js` 里有对应的 JS 实现，Demo 数据验证误差 < 1 HKD。

---

## Demo 数据对账

Demo 是一套故意"不健康"的香港家庭画像：有房有按揭、现金偏薄、工资单一、房产占净值过高。用来演示黄灯和红灯，不是模范家庭。

| 指标 | 公式 | Demo 结果 | 灯 |
|---|---|---|---|
| 总资产 A | Σ 资产 (折 HKD) | HK$6,106,000 | — |
| 总负债 L | Σ 负债 (折 HKD) | HK$2,445,000 | — |
| **净值 E** | A − L | **HK$3,661,000** | — |
| 高流动性资产 A_high | liquidity=high | HK$119,000 | — |
| 流动性月数 LIM | A_high / EXP_ess | **3.40 个月** | 🟡 黄 |
| **应急金缺口 GAP** | max(0, 6×EXP_ess − A_high) | **HK$91,000** | 有缺口 |
| 杠杆 LEV | L / A | 40.04% | 🟡 黄 |
| DSTI | DS / INC | 43.75% | 🟡 黄 |
| 房产 / 净值 | — | 150% | 🔴 红 |
| **综合灯** | 取最差 | — | 🔴 **红** |

**汇率口径**：1 USD = 7.80 HKD（`as_of` 见 `data/demo/fx.csv`）。

**应急金缺口推导**（GAP = HK$91,000）：

```
目标储备 = 6 个月 × 月必要支出 HK$35,000 = HK$210,000
已持有   = 高流动性资产                   = HK$119,000
───────────────────────────────────────────────
缺口     = max(0, 210K − 119K)            = HK$91,000
```

---

## 口径摘要

金额一律先折港币再汇总。

| 指标 | 公式 | 备注 |
|---|---|---|
| 净值 | `E = A − L` | — |
| 杠杆 | `LEV = L / A` | — |
| 流动性月数 | `LIM = A_high / EXP_ess` | 分母=标了 essential 的月度支出 |
| 应急金缺口 | `GAP = max(0, 6 × EXP_ess − A_high)` | — |
| 偿债比率 | `DSTI = DS / INC` | DS 来自 debt_service=1 的支出 |
| 投资集中度 | `investRatio = 投资类资产 / E` | E ≤ 0 时不输出 |
| 类别集中度 | `maxCatRatio = 最大类别 / E` | E ≤ 0 时不输出，直接红灯 |

**安全闸**：必要支出为 0、或缺汇率、或资产总额为 0 —— **禁止出绿灯**，UI 显示"数据不足"。

完整公式、限额阈值、压力冲击字段以 `.trae/rules/project_rules.md` 和 `config/*.yaml` 为准。

---

## 7 条风险限额

| ID | 名称 | 🟢 绿 | 🟡 黄 | 🔴 红 |
|---|---|---|---|---|
| LIM | 流动性月数 | ≥ 6 个月 | 3–6 个月 | < 3 个月 |
| LEV | 杠杆 L/A | ≤ 40% | 40–60% | > 60% |
| E | 净值 | > 0 | — | < 0 |
| DSTI | 偿债比率 | ≤ 40% | 40–50% | > 50% |
| INVEST | 投资 / 净值 | ≤ 60% | 60–80% | > 80% |
| CONC | 单一类别 / 净值 | ≤ 70% | 70–90% | > 90% |
| INCOME | 收入单一性 | 多来源 或 LIM≥6 | 单来源 且 3≤LIM<6 | 单来源 且 LIM<3 |

综合灯 = 所有限额中最差的等级（绿 < 黄 < 红）。

---

## 10 个预置压力情景

| ID | 名称 | 冲击 |
|---|---|---|
| base | 基准 | 无 |
| jobloss3 / jobloss6 | 失业视角 | 收入 → 0 |
| invest20 / invest40 | 投资下跌 | 投资资产 × 0.8 / × 0.6 |
| property15 / property30 | 房价下跌 | 房产 × 0.85 / × 0.70 |
| rate20 | 供款上升 | 债务供款 × 1.2 |
| combo_job_invest | 失业 + 投资跌 20% ⭐默认 | 收入→0, 投资×0.8 |
| combo_housing | 房价跌 15% + 利率 +20% | 房产×0.85, 供款×1.2 |

HTML 版额外支持 **自定义滑块**：6 个冲击系数（income_mult / property_mult / invest_mult / debt_service_mult / essential_exp_mult / liability_mult）实时拖动。

---

## 自己的数据

### HTML 版（最方便）

1. 打开 `[`web/index.html`]([web/index.html](https://jhuanya.github.io/household-risk-desk/web/index.html))`
2. 进入 📝 **数据输入** 页
3. 直接在表格里改数值、加行、删行，汇率也可以编辑
4. 数据自动存浏览器 localStorage，换浏览器要手动复制
5. 想重来？点「↺ 重置为 Demo 数据」

### Streamlit 版

1. 复制 Demo 三张表：`cp data/demo/*.csv data/local/`
2. 改金额，**不要改列名**
3. 界面（未来会加）或代码里切换到 `data/local/`
4. 确认 `data/local/` 已被 `.gitignore`

**应急金口径提示**：只统计 `liquidity=high` 的资产。股票/基金标 `medium`，自住房/强积金标 `low`。

---

## 测试

- [x] Demo 可启动，所有页面能打开
- [x] 净值、LIM、GAP 与 `DEMO_CHECK.md` 一致（误差 < 1 HKD）
- [x] 删掉 USD 汇率行后，**不得假绿灯**
- [x] 必要支出为 0 时，流动性指标显示"不可用"
- [x] 基准综合灯为红；联合压力情景不优于基准
- [x] HTML 版输入负数/非法值 → 阻断计算 + 红色高亮
- [x] HTML 版与 Streamlit 版数值一致

限额工具定位 → 风险事件定义 → 现状灯号 → 失业+投资下跌 → 需补多少现金 → 局限（手工数据、粗冲击）。


---

## 文档

| 文件 | 用途 |
|---|---|
| `.trae/rules/project_rules.md` | 给 AI 的硬约束（公式、字段名、限额阈值） |
| `data/DEMO_CHECK.md` | Demo 手工对账（精确到 1 HKD） |
| `config/limits.yaml` | 7 条限额的阈值配置 |
| `config/scenarios.yaml` | 10 个压力情景的冲击系数 |

---


---

> ⚠️ 不构成投资、信贷或税务建议。限额与情景是个人风险偏好设定，不是预测。
