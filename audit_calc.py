"""
计算审计脚本 —— 验证所有核心计算的正确性
手动复算每一个指标，和代码输出逐项比对
"""
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import pandas as pd
from src.data_loader import load_all_data
from src.metrics import compute_metrics
from src.limits import compute_all_limits, load_limits_config
from src.scenarios import get_all_scenarios, compare_scenarios

all_pass = True

print("=" * 70)
print("第一部分: 基础数据 —— 手动验证 HKD 折算")
print("=" * 70)
household, cashflow, fx_df, fx_rates, as_of = load_all_data()
print(f"汇率表: {fx_rates}")
print(f"汇率日期: {as_of}")

print("\n--- household.csv 逐行验证 ---")
for _, row in household.iterrows():
    curr = row["currency"]
    amt = row["amount"]
    manual_hkd = amt * fx_rates.get(curr, 1.0)
    actual_hkd = row["hkd"]
    ok = "✅" if abs(manual_hkd - actual_hkd) < 0.01 else "❌ MISMATCH"
    if ok.startswith("❌"): all_pass = False
    print(f"  {row['item_id']:20s} {amt:>12,.0f} {curr} × {fx_rates.get(curr,1.0):.2f} = {manual_hkd:>14,.0f} [实际 {actual_hkd:>14,.0f}] {ok}")

print("\n--- cashflow.csv 逐行验证 ---")
for _, row in cashflow.iterrows():
    curr = row["currency"]
    amt = row["monthly_amount"]
    manual_hkd = amt * fx_rates.get(curr, 1.0)
    actual_hkd = row["hkd"]
    ok = "✅" if abs(manual_hkd - actual_hkd) < 0.01 else "❌ MISMATCH"
    if ok.startswith("❌"): all_pass = False
    print(f"  {row['item_id']:20s} {amt:>12,.0f} {curr} × {fx_rates.get(curr,1.0):.2f} = {manual_hkd:>14,.0f} [实际 {actual_hkd:>14,.0f}] {ok}")

print("\n" + "=" * 70)
print("第二部分: 基准指标 —— 手动复算 vs compute_metrics()")
print("=" * 70)
metrics = compute_metrics(household, cashflow)

assets = household[household["type"] == "asset"]
liabs = household[household["type"] == "liability"]

A_manual = assets["hkd"].sum()
L_manual = liabs["hkd"].sum()
E_manual = A_manual - L_manual
A_high_manual = assets[assets["liquidity"] == "high"]["hkd"].sum()
A_invest_manual = assets[assets["category"] == "investment"]["hkd"].sum()
A_property_manual = assets[assets["category"] == "property"]["hkd"].sum()
A_cash_manual = assets[assets["category"] == "cash"]["hkd"].sum()
A_other_manual = assets[assets["category"] == "other"]["hkd"].sum()

cat_totals_manual = {}
for cat in assets["category"].unique():
    cat_totals_manual[cat] = assets[assets["category"] == cat]["hkd"].sum()

max_cat_manual = max(cat_totals_manual, key=cat_totals_manual.get)
max_cat_amt_manual = cat_totals_manual[max_cat_manual]

INC_manual = cashflow[cashflow["direction"] == "in"]["hkd"].sum()
EXP_ess_manual = cashflow[(cashflow["direction"] == "out") & (cashflow["essential"] == 1)]["hkd"].sum()
DS_manual = cashflow[(cashflow["direction"] == "out") & (cashflow["debt_service"] == 1)]["hkd"].sum()

LIM_manual = A_high_manual / EXP_ess_manual if EXP_ess_manual > 0 else None
GAP_manual = max(0, 6 * EXP_ess_manual - A_high_manual) if EXP_ess_manual > 0 else None
LEV_manual = L_manual / A_manual if A_manual > 0 else float("inf")
DSTI_manual = DS_manual / INC_manual if INC_manual > 0 else (float("inf") if DS_manual > 0 else None)
investRatio_manual = A_invest_manual / E_manual if E_manual > 0 else None
propertyRatio_manual = A_property_manual / E_manual if E_manual > 0 else None
maxCatRatio_manual = max_cat_amt_manual / E_manual if E_manual > 0 else None

def check(label, manual, computed, tol=0.005):
    global all_pass
    if manual is None and computed is None:
        return "✅"
    if manual is None or computed is None:
        all_pass = False
        return f"❌ manual={manual}, computed={computed}"
    if manual == float("inf") and computed == float("inf"):
        return "✅ inf"
    if manual == float("inf") or computed == float("inf"):
        all_pass = False
        return f"❌ inf mismatch"
    if manual == 0 and computed == 0:
        return "✅"
    diff = abs(manual - computed)
    rel = diff / abs(manual)
    ok = rel < tol
    if not ok: all_pass = False
    return ("✅" if ok else f"❌ diff={diff:,.2f} rel={rel:.4%}")

results = [
    ("A  总资产",         A_manual,          metrics["A"]),
    ("L  总负债",         L_manual,          metrics["L"]),
    ("E  净值",           E_manual,          metrics["E"]),
    ("A_high 高流动性",   A_high_manual,     metrics["A_high"]),
    ("A_invest 投资",     A_invest_manual,   metrics["A_invest"]),
    ("A_property 房产",   A_property_manual, metrics["A_property"]),
    ("A_cash 现金",       A_cash_manual,     metrics["A_cash"]),
    ("A_other 其他",      A_other_manual,    metrics["A_other"]),
    ("INC 月收入",        INC_manual,        metrics["INC"]),
    ("EXP_ess 必要支出",  EXP_ess_manual,    metrics["EXP_ess"]),
    ("DS 债务供款",       DS_manual,         metrics["DS"]),
    ("LIM 流动性月数",    LIM_manual,        metrics["LIM"]),
    ("GAP 应急金缺口",    GAP_manual,        metrics["GAP"]),
    ("LEV 杠杆",          LEV_manual,        metrics["LEV"]),
    ("DSTI 偿债比",       DSTI_manual,       metrics["DSTI"]),
    ("investRatio",       investRatio_manual,    metrics["investRatio"]),
    ("propertyRatio",     propertyRatio_manual,  metrics["propertyRatio"]),
    ("maxCatRatio",       maxCatRatio_manual,    metrics["maxCatRatio"]),
]

for label, m, c in results:
    status = check(label, m, c)
    print(f"  {label:20s}: manual={str(m):>14s}  computed={str(c):>14s}  {status}")

print("\n--- catTotals 字典比对 ---")
for cat, amt in cat_totals_manual.items():
    comp_amt = metrics["catTotals"].get(cat, 0)
    ok = check(cat, amt, comp_amt)
    print(f"  {cat:12s}: manual={amt:>14,.2f}  computed={comp_amt:>14,.2f}  {ok}")

print("\n" + "=" * 70)
print("第三部分: 限额判断 —— 手动 vs compute_all_limits()")
print("=" * 70)

limits = compute_all_limits(metrics)
config = load_limits_config()

lim_val = metrics["LIM"]
lim_expected = "red" if lim_val < config["lim_red_below"] else ("yellow" if lim_val < config["lim_yellow_below"] else "green")

lev_val = metrics["LEV"]
lev_expected = "red" if lev_val > config["lev_red_above"] else ("yellow" if lev_val > config["lev_yellow_above"] else "green")

e_val = metrics["E"]
e_expected = "red" if e_val < 0 else "green"

dsti_val = metrics["DSTI"]
if dsti_val == float("inf"):
    dsti_expected = "red"
elif dsti_val is None:
    dsti_expected = "green"
else:
    dsti_expected = "red" if dsti_val > config["dsti_red_above"] else ("yellow" if dsti_val > config["dsti_yellow_above"] else "green")

invest_val = metrics["investRatio"]
if invest_val is None:
    invest_expected = "green" if e_val > 0 else "red"
elif e_val <= 0:
    invest_expected = "red"
else:
    invest_expected = "red" if invest_val > config["invest_red_above"] else ("yellow" if invest_val > config["invest_yellow_above"] else "green")

conc_val = metrics["maxCatRatio"]
if conc_val is None:
    conc_expected = "green" if e_val > 0 else "red"
elif e_val <= 0:
    conc_expected = "red"
else:
    conc_expected = "red" if conc_val > config["concentration_red_above"] else ("yellow" if conc_val > config["concentration_yellow_above"] else "green")

src = metrics["incomeSources"]
if src <= 1 and metrics.get("limAvailable", True) and lim_val is not None:
    if lim_val < 3: income_expected = "red"
    elif lim_val < config["lim_target_months"]: income_expected = "yellow"
    else: income_expected = "green"
else:
    income_expected = "green"

expected = {
    "LIM": lim_expected, "LEV": lev_expected, "E": e_expected,
    "DSTI": dsti_expected, "INVEST": invest_expected,
    "CONC": conc_expected, "INCOME": income_expected,
}

for l in limits["limits"]:
    lid = l["id"]
    exp = expected.get(lid, "?")
    act = l["status"]
    ok = "✅" if exp == act else "❌ MISMATCH"
    if ok.startswith("❌"): all_pass = False
    print(f"  {lid:8s}: expected={exp:7s}  actual={act:7s}  value={l['display']:20s}  {ok}")

rank = {"green": 0, "yellow": 1, "red": 2}
overall_expected = expected["LIM"]
for v in expected.values():
    if rank[v] > rank[overall_expected]:
        overall_expected = v
overall_actual = limits["overall"]
ok = "✅" if overall_expected == overall_actual else "❌ MISMATCH"
if ok.startswith("❌"): all_pass = False
print(f"\n  OVERALL: expected={overall_expected}  actual={overall_actual}  {ok}")

# 告警列表应 = 非绿灯项
alerts_expected = [k for k, v in expected.items() if v != "green"]
alerts_actual = [l["id"] for l in limits["alerts"]]
alerts_ok = set(alerts_expected) == set(alerts_actual)
if not alerts_ok: all_pass = False
print(f"  ALERTS: expected={alerts_expected}  actual={alerts_actual}  {'✅' if alerts_ok else '❌'}")

print("\n" + "=" * 70)
print("第四部分: 压力情景 —— 冲击系数应用验证")
print("=" * 70)
scenarios = get_all_scenarios()
TARGET_SCENARIOS = ("base", "combo_job_invest", "combo_housing", "invest20", "property15")

for sc in scenarios:
    sid = sc["id"]
    if sid not in TARGET_SCENARIOS:
        continue
    shock = {k: sc.get(k, 1.0) for k in
             ["income_mult","essential_exp_mult","invest_mult","property_mult","debt_service_mult","liability_mult"]}
    stress = compute_metrics(household, cashflow, shock)
    print(f"\n--- {sc['name']} (id={sid}) ---")
    print(f"  冲击系数: {shock}")

    # 手动重算 A
    def asset_hkd_shock(row):
        if row["category"] == "investment": return row["hkd"] * shock["invest_mult"]
        if row["category"] == "property": return row["hkd"] * shock["property_mult"]
        return row["hkd"]
    A_manual_shock = assets.apply(asset_hkd_shock, axis=1).sum()
    L_manual_shock = L_manual * shock["liability_mult"]
    E_manual_shock = A_manual_shock - L_manual_shock
    INC_manual_shock = INC_manual * shock["income_mult"]
    DS_manual_shock = DS_manual * shock["debt_service_mult"]

    # 重算 EXP_ess
    EXP_ess_manual_shock = 0.0
    for _, row in cashflow.iterrows():
        if row["direction"] == "out" and row.get("essential", 0) == 1:
            base_mult = shock["essential_exp_mult"]
            if row.get("debt_service", 0) == 1:
                EXP_ess_manual_shock += row["hkd"] * base_mult * shock["debt_service_mult"]
            else:
                EXP_ess_manual_shock += row["hkd"] * base_mult

    LIM_ms = A_high_manual / EXP_ess_manual_shock if EXP_ess_manual_shock > 0 else None
    GAP_ms = max(0, 6 * EXP_ess_manual_shock - A_high_manual) if EXP_ess_manual_shock > 0 else None
    LEV_ms = L_manual_shock / A_manual_shock if A_manual_shock > 0 else float("inf")
    DSTI_ms = DS_manual_shock / INC_manual_shock if INC_manual_shock > 0 else (float("inf") if DS_manual_shock > 0 else None)

    checks = [
        ("A  总资产",    A_manual_shock,  stress["A"]),
        ("L  总负债",    L_manual_shock,  stress["L"]),
        ("E  净值",      E_manual_shock,  stress["E"]),
        ("INC",          INC_manual_shock, stress["INC"]),
        ("EXP_ess",      EXP_ess_manual_shock, stress["EXP_ess"]),
        ("DS",           DS_manual_shock,  stress["DS"]),
        ("LIM",          LIM_ms, stress["LIM"]),
        ("GAP",          GAP_ms, stress["GAP"]),
        ("LEV",          LEV_ms, stress["LEV"]),
        ("DSTI",         DSTI_ms, stress["DSTI"]),
    ]
    for label, m, c in checks:
        ok = check(label, m, c)
        print(f"  {label:12s}: manual={str(m):>20s}  computed={str(c):>20s}  {ok}")

    # 失业情景辅助数据验证
    if shock["income_mult"] == 0:
        unemp = stress.get("unemployment")
        if unemp:
            need3_expected = EXP_ess_manual_shock * 3
            need6_expected = EXP_ess_manual_shock * 6
            gap3_expected = max(0, need3_expected - A_high_manual)
            gap6_expected = max(0, need6_expected - A_high_manual)
            print(f"  [失业辅助] need3: manual={need3_expected:,.0f} actual={unemp['need3']:,.0f} {'✅' if abs(need3_expected-unemp['need3'])<0.01 else '❌'}")
            print(f"  [失业辅助] gap6:  manual={gap6_expected:,.0f} actual={unemp['gap6']:,.0f} {'✅' if abs(gap6_expected-unemp['gap6'])<0.01 else '❌'}")

print("\n" + "=" * 70)
print("第五部分: compare_scenarios 击穿判断逻辑")
print("=" * 70)

base_m = compute_metrics(household, cashflow, {"income_mult":1.0,"essential_exp_mult":1.0,"invest_mult":1.0,"property_mult":1.0,"debt_service_mult":1.0,"liability_mult":1.0})
base_l = compute_all_limits(base_m)

stress_shock = {"income_mult":0.0,"essential_exp_mult":1.0,"invest_mult":0.8,"property_mult":1.0,"debt_service_mult":1.0,"liability_mult":1.0}
stress_m = compute_metrics(household, cashflow, stress_shock)
stress_l = compute_all_limits(stress_m)
result = compare_scenarios(base_m, stress_m, base_l, stress_l)

print(f"对比: 基准 vs 失业+投资-20%")
print(f"  基准综合灯: {result['overall_baseline']}")
print(f"  压力综合灯: {result['overall_stress']}")
print(f"  综合灯变化: {result['overall_changed']}")
print(f"  击穿项: {len(result['breaches'])}")
for b in result["breaches"]:
    print(f"    - {b['id']}: {b['baseline_status']} → {b['stress_status']}  {b['name']}")

print("\n--- 击穿逻辑验证: stress灯变差 且 stress为red 且 base不是red ---")
expected_breaches = []
base_limit_dict = {l["id"]: l["status"] for l in base_l["limits"]}
stress_limit_dict = {l["id"]: l["status"] for l in stress_l["limits"]}
for lid in stress_limit_dict:
    ss = stress_limit_dict[lid]
    bs = base_limit_dict.get(lid, "green")
    if ss == "red" and bs != "red":
        expected_breaches.append(lid)
actual_breaches = [b["id"] for b in result["breaches"]]
ok = set(expected_breaches) == set(actual_breaches)
if not ok: all_pass = False
print(f"  expected breaches: {expected_breaches}")
print(f"  actual breaches:   {actual_breaches}  {'✅' if ok else '❌'}")

print("\n" + "=" * 70)
if all_pass:
    print("🎉 全部计算验证通过！没有发现数据计算错误。")
else:
    print("⚠️  存在 MISMATCH！请检查上方 ❌ 标记的项目。")
print("=" * 70)
