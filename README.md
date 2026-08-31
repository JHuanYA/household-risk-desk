# 家庭 / 个人财务风险驾驶舱

**Household Financial Risk Desk** · PRD-HFRD-001

给个人或家庭用的流动性与偿付风险控制台：看清家底、限制风险、在压力情景下判断会不会断现金流，并给出可执行的处置建议。

本仓库是转行风控作品集项目，也是可以每月自己用的工具。默认运行虚构 Demo 家庭，不连接银行，不拉取行情。

> 不构成投资、信贷或税务建议。限额与情景是个人风险偏好设定，不是预测。

---

## 这是什么 / 不是什么

| 是 | 不是 |
|---|---|
| 家庭资产负债表 + 现金流 | 记账、预算信封、消费分类 |
| 流动性、杠杆、DSTI、集中度 | 个股 VaR、组合优化、荐股 |
| 可配置限额（绿 / 黄 / 红） | 银行审批、征信评分 |
| 压力测试与缺口建议 | 银行 API、PDF 账单识别 |

风险闭环固定为五步：**定义风险事件 → 计量现状 → 设定限额 → 压力测试 → 处置建议**。

两件被定义为“出事”：

1. **流动性断裂**：高流动性资产覆盖不了目标月数的必要支出（默认 6 个月）
2. **偿付危机**：净资产小于 0，或压力后净资产小于 0

---

## 界面（5 页）

1. **总览** — 净值、杠杆、流动性月数、应急金缺口、DSTI、综合灯、告警
2. **资产负债表** — 原币与港币、流动性分级、分类汇总
3. **现金流** — 收入、必要 / 非必要支出、债务供款、月结余
4. **压力测试** — 预置情景对照；默认「失业 + 投资下跌 20%」
5. **限额与假设** — 阈值、当前值、原因句、口径说明

---

## 仓库结构

```text
household-risk-desk/
├── README.md
├── .gitignore
├── .trae/rules/project_rules.md   # Trae 必须遵守的范围与公式
├── docs/                          # 放入 PRD（Markdown 或 PDF）
├── config/
│   ├── limits.yaml                # 风险限额
│   └── scenarios.yaml             # 压力情景
├── data/
│   ├── demo/                      # 虚构家庭（可进 Git）
│   │   ├── household.csv
│   │   ├── cashflow.csv
│   │   ├── fx.csv
│   │   └── DEMO_CHECK.md
│   └── local/                     # 真实数据（禁止提交）
├── src/
│   ├── data/                      # 读表、校验、折港币
│   ├── metrics/                   # 公式
│   ├── limits/                    # 灯号
│   └── stress/                    # 压力测试
├── tests/
└── app/                           # Web UI
```

若本地目录名不同，以实际代码为准，但 **CSV 字段名不得更改**。

---

## 数据怎么用

### Demo（默认）

路径：`data/demo/`

这是一套故意“不健康”的香港家庭画像：有房有按揭、现金偏薄、工资单一、房产占净值过高。用来演示黄灯和红灯，不是模范家庭。

对账见 [`data/demo/DEMO_CHECK.md`](data/demo/DEMO_CHECK.md)。实现后数字误差应小于 1 港币。

| 指标 | Demo 结果 | 灯 |
|---|---|---|
| 资产 / 负债 / 净值 | 6,106,000 / 2,445,000 / 3,661,000 | — |
| 高流动性资产 | 119,000 | — |
| 流动性月数 | 3.40 个月 | 黄 |
| 应急金缺口（目标 6 个月） | 91,000 | 有缺口 |
| 杠杆 L/A | 40.04% | 黄 |
| DSTI | 43.75% | 黄 |
| 房产 / 净值 | 150% | 红 |
| 综合灯 | — | **红** |

汇率口径：`1 USD = 7.80 HKD`（见 `fx.csv` 的 `as_of`）。

### 自己的数据（可选）

1. 复制 Demo 三张表到 `data/local/`
2. 改金额，不要改列名
3. 界面切换到「本地数据」
4. 确认 `data/local/` 已被 `.gitignore`

应急金只统计 `liquidity=high`。股票、基金应标 `medium`，自住房和强积金应标 `low`。

---

## 口径摘要

金额一律先折港币再汇总。

- 净值 `E = A - L`
- 杠杆 `LEV = L / A`
- 流动性月数 `LIM = A_high / EXP_ess`
- 应急金缺口 `GAP = max(0, 6 × EXP_ess - A_high)`
- 偿债比率 `DSTI = DS / INC`
- 集中度分母用净值 `E`，不用总资产
- `E ≤ 0` 时不输出集中度百分比，直接红灯
- 必要支出为 0，或缺汇率时：**禁止出绿灯**

完整公式、限额阈值、压力冲击字段以 PRD 第 8–9 章和 `.trae/rules/project_rules.md` 为准。

---

## 本地运行

先确认已安装 Python 3.11+（若 UI 为 Node 项目，按其 `package.json` 运行）。

```bash
git clone <your-repo-url> household-risk-desk
cd household-risk-desk

python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
```

启动命令取决于你的前端实现，任选与仓库一致的一种：

```bash
# Streamlit
streamlit run app/app.py

# 或 FastAPI + 前端
uvicorn app.main:app --reload

# 或 Node 前端
npm install && npm run dev
```

浏览器打开终端提示的本地地址。顶部应显示 **Demo** 字样。

没有 `requirements.txt` 时，先让 Trae 根据现有代码生成，不要手写一堆用不到的包。

---

## 用 Trae 继续开发

1. 用 Trae 打开本仓库，确认已连接 GitHub。
2. 对话时带上：`@.trae/rules/project_rules.md` `@data/demo/DEMO_CHECK.md`
3. 一次只做一个里程碑：数据层 → 指标 → 限额灯 → 接到已有 UI → 压力测试 → README/假设文档。
4. 不要开 SOLO 整站重写界面。
5. 每个里程碑单独分支、单独 commit。

推荐第一句：

```text
@.trae/rules/project_rules.md
@data/demo/DEMO_CHECK.md
只分析、不要改代码：对照 DEMO_CHECK，列出当前还缺的计算与校验。
```

---

## 测试与验收

最低要求：

- [ ] Demo 可启动，五个页面都能打开
- [ ] 净值、LIM、GAP 与 `DEMO_CHECK.md` 一致（误差 < 1 HKD）
- [ ] 删掉 `fx.csv` 中的 USD 行后，总览不得假绿灯
- [ ] 必要支出为 0 时，流动性指标显示不可用
- [ ] 基准综合灯为黄或红；联合压力情景不优于基准
- [ ] 仓库无真实姓名、账号、真实账单

面试演示约 6 分钟：限额工具定位 → 风险事件定义 → 现状灯号 → 失业+投资下跌 → 需补多少现金 → 局限（手工数据、粗冲击）。

---

## 隐私与 Git

`.gitignore` 至少包含：

```gitignore
data/local/
.venv/
__pycache__/
.env
node_modules/
```

建议仓库保持 **Private**。对外展示只用 Demo。

---

## 文档

| 文件 | 用途 |
|---|---|
| `.trae/rules/project_rules.md` | 给 AI 的硬约束 |
| `data/demo/DEMO_CHECK.md` | Demo 手工对账 |
| `docs/PRD_HFRD_V1.0.md`（或 PDF） | 完整需求 |

本产品与「组合市场风险看板」互相独立，不要做到同一个 App 里。
