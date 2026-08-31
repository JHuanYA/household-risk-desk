# 家庭 / 个人财务风险驾驶舱 — Trae 项目规则

你是本仓库的实现助手，不是产品经理。需求已经冻结。先读规则，再改代码。

## 1. 产品边界

- 本仓库只实现「家庭 / 个人财务风险驾驶舱」（Household Financial Risk Desk）。
- 唯一需求基准：`docs/PRD_HFRD_V1.0.md`（若尚未放入，以本规则 + `data/demo` 字段为准，不得自行扩范围）。
- 文档编号：PRD-HFRD-001。汇总货币：港币（HKD）。
- 这是风险管理工具，不是记账 App、不是投资顾问、不是交易系统。

## 2. 禁止事项（违反即停，先说明再等用户确认）

禁止实现或引入：

- 消费记账、预算信封、商户分类统计
- 银行 / 券商 / 支付 API、爬虫拉账单、PDF 月结 OCR
- 个股/ETF 行情拉取（yfinance、AKShare 等）
- VaR、ES、Beta、相关性、波动率、回撤曲线
- 贷款审批、征信评分、反欺诈
- 荐股、自动再平衡、收益预测、税务优化
- 把投资明细拆成组合风险模块（那是独立产品，不在本仓库）
- 多用户云同步、账号体系、把真实家庭数据写入 Git

投资资产在本产品中只是资产负债表里 `category=investment` 的市值，压力测试用冲击系数，不算证券风险。

## 3. 工作方式

- 一次只做用户指定的一个里程碑，不要重构整个项目，不要重写已有 UI 样式。
- 先给计划（改哪些文件、不改哪些），等用户确认后再写代码。
- 配置与计算分离：限额在 `config/limits.yaml`，情景在 `config/scenarios.yaml`，公式在 `src/metrics`，界面不得重写公式。
- 计算必须可脱离 UI 运行，并配最小测试/对账。
- 真实数据只允许出现在 `data/local/`，且必须被 `.gitignore`。默认启动 `data/demo/`。
- 界面必须标明当前是 Demo 还是本地数据。
- 不要调用外部大模型在运行时生成风险评语。态势句用规则拼接。

## 4. 数据字段（名称冻结，只许加字段不许改名）

### data/demo/household.csv

`item_id,name,type,category,amount,currency,liquidity,owner,monthly_payment,note`

- `type`：`asset` | `liability`
- 资产 `category`：`cash` | `investment` | `property` | `other`
- 负债 `category`：`mortgage` | `consumer` | `other_debt`
- 资产必须有 `liquidity`：`high` | `medium` | `low`
- 负债金额用正数表示余额
- `currency`：`HKD` | `USD` | `CNY`（出现非 HKD 时 `fx.csv` 必须有汇率）

### data/demo/cashflow.csv

`item_id,name,direction,monthly_amount,currency,essential,debt_service,source_rank,note`

- `direction`：`in` | `out`
- `essential`、`debt_service`：`0` 或 `1`
- 流出的必要支出：`essential=1`
- DSTI 分母用收入合计，分子用 `debt_service=1` 的流出合计
- 收入来源数：`direction=in` 且金额>0 的不同 `source_rank` 个数

### data/demo/fx.csv

`currency,hkd_per_unit,as_of`

- 含义：1 单位外币兑港币
- HKD 可省略，默认 1
- 缺汇率：校验失败，禁止继续出完整绿灯总览

## 5. 公式（数字宪法，不得擅自改分母）

金额一律先折港币：`hkd = amount * hkd_per_unit`。

- `A` = 资产合计
- `L` = 负债合计
- `E` = `A - L`（净值）
- `A_high` = `liquidity=high` 的资产合计  
  应急金只承认 high。`category=investment` 标成 high 时必须警告。
- `A_invest` = `category=investment`
- `A_property` = `category=property`
- `INC` = 流入月度合计
- `EXP_ess` = `direction=out` 且 `essential=1` 的合计（可含供款）
- `DS` = `debt_service=1` 的流出合计
- `LEV` = `L / A`；`A=0` 视为无穷大并红灯
- `LIM` = `A_high / EXP_ess`（月）
- `LID` = `LIM * 30`（天）
- `GAP` = `max(0, LIM_target * EXP_ess - A_high)`，默认 `LIM_target=6`
- `DSTI` = `DS / INC`
- 集中度分母用净值 `E`，不用总资产 `A`
- `E <= 0`：集中度不输出百分比，直接按偿付危机红灯
- `EXP_ess = 0`：流动性指标标记为不可用，禁止绿灯
- `INC = 0` 且 `DS > 0`：DSTI 红灯或显示不适用，禁止除零后当正常值

## 6. 默认限额与灯号

绿 = 达标；黄 = 破目标未破硬限额；红 = 破硬限额或计算异常。综合灯取最差（红 > 黄 > 绿）。

| 限额 | 黄 | 红 |
|---|---|---|
| 流动性月数 LIM | < 6 | < 3 |
| 杠杆 L/A | > 40% | > 60% |
| 净值 E | — | < 0 |
| DSTI | > 40% | > 50% |
| 投资 / 净值 | > 60% | > 80% |
| 单一类别 / 净值 | > 70% | > 90% |
| 收入来源≤1 且 LIM<6 | 黄 | 再叠加 LIM<3 为红 |

原因句必须带数值，禁止「请注意风险」这类空话。

## 7. 压力测试

- 冲击作用在内存副本，不得改原始 CSV。
- 冲击字段：`income_mult`、`essential_exp_mult`、`invest_mult`、`property_mult`、`debt_service_mult`、`liability_mult`。
- 失业情景不得只靠「收入×0 再算 DSTI」糊弄。必须同时输出：
  - 存量视角：`A_high` 能覆盖几个月必要支出
  - 3 个月缺口 = `max(0, 3*EXP_ess - A_high)`
  - 6 个月缺口 = `max(0, 6*EXP_ess - A_high)`
  - 若 LIM < 目标月数，该失业情景未通过
- 默认选中联合情景：失业 + 投资市值 ×0.8。
- 页面对照至少包含：E、A、L、A_high、LIM、GAP、LEV、DSTI、综合灯、击穿清单。

## 8. 验收红线

- Demo 启动后基准综合灯必须为黄或红，应急金缺口 GAP 不得为 0。
- 缺少 USD 汇率时不得显示完整绿灯结果。
- 必要支出为 0 时流动性不能绿灯。
- 仓库不得包含真实姓名、账号、真实账单。
- README 必须写明：不构成投资、信贷或税务建议。

## 9. 对用户指令的默认理解

用户说「接数据 / 做指标 / 做限额 / 做压力 / 接到 UI」时，分别只做对应层。  
用户没有点名重做 UI 时，保留现有页面结构和样式，只替换假数据。
