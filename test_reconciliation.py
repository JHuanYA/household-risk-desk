"""
计算逻辑对账测试
验证 Python 计算结果是否与 DEMO_CHECK.md 一致
"""

import sys
import os

# 直接从 src 导入，不走 app.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app", "src"))

from data_loader import load_all_data
from metrics import compute_metrics
from limits import compute_all_limits


def test_reconciliation():
    """对账测试"""
    print("=" * 60)
    print("家庭财务风险驾驶舱 - 计算逻辑对账测试")
    print("=" * 60)

    # 数据目录
    data_dir = os.path.join(os.path.dirname(__file__), "data", "demo")

    print(f"\n汇率日期: {as_of}")
    print(f"汇率: {fx_rates}")

    # 计算指标
    metrics = compute_metrics(household, cashflow)
    limits_result = compute_all_limits(metrics)

    # DEMO_CHECK.md 预期值
    expected = {
        "A": 6106000,
        "L": 2445000,
        "E": 3661000,
        "A_high": 119000,
        "EXP_ess": 35000,
        "DS": 21000,
        "INC": 48000,
        "LIM": 3.40,
        "GAP": 91000,
        "LEV": 0.4004,
        "DSTI": 0.4375,
    }

    print("\n" + "=" * 60)
    print("资产负债表对账")
    print("=" * 60)

    checks = [
        ("资产 A", metrics.get("A"), expected["A"]),
        ("负债 L", metrics.get("L"), expected["L"]),
        ("净值 E", metrics.get("E"), expected["E"]),
        ("高流动性 A_high", metrics.get("A_high"), expected["A_high"]),
    ]

    for name, actual, exp in checks:
        diff = abs(actual - exp)
        status = "✅" if diff < 1 else "❌"
        print(f"{status} {name}: 实际={actual:,.0f}, 预期={exp:,.0f}, 误差={diff:.0f}")

    print("\n" + "=" * 60)
    print("现金流对账")
    print("=" * 60)

    cashflow_checks = [
        ("月收入 INC", metrics.get("INC"), expected["INC"]),
        ("必要支出 EXP_ess", metrics.get("EXP_ess"), expected["EXP_ess"]),
        ("债务供款 DS", metrics.get("DS"), expected["DS"]),
    ]

    for name, actual, exp in cashflow_checks:
        diff = abs(actual - exp)
        status = "✅" if diff < 1 else "❌"
        print(f"{status} {name}: 实际={actual:,.0f}, 预期={exp:,.0f}, 误差={diff:.0f}")

    print("\n" + "=" * 60)
    print("风险指标对账")
    print("=" * 60)

    # LIM
    lim_diff = abs(metrics.get("LIM", 0) - expected["LIM"])
    print(f"{'✅' if lim_diff < 0.01 else '❌'} 流动性月数 LIM: 实际={metrics.get('LIM', 0):.2f}, 预期={expected['LIM']:.2f}, 误差={lim_diff:.4f}")

    # GAP
    gap_diff = abs(metrics.get("GAP", 0) - expected["GAP"])
    print(f"{'✅' if gap_diff < 1 else '❌'} 应急金缺口 GAP: 实际={metrics.get('GAP', 0):,.0f}, 预期={expected['GAP']:,.0f}, 误差={gap_diff:.0f}")

    # LEV
    lev_diff = abs(metrics.get("LEV", 0) - expected["LEV"])
    print(f"{'✅' if lev_diff < 0.0001 else '❌'} 杠杆 LEV: 实际={metrics.get('LEV', 0):.4f}, 预期={expected['LEV']:.4f}, 误差={lev_diff:.6f}")

    # DSTI
    dsti_diff = abs(metrics.get("DSTI", 0) - expected["DSTI"])
    print(f"{'✅' if dsti_diff < 0.0001 else '❌'} DSTI: 实际={metrics.get('DSTI', 0):.4f}, 预期={expected['DSTI']:.4f}, 误差={dsti_diff:.6f}")

    print("\n" + "=" * 60)
    print("灯号验证")
    print("=" * 60)

    # 综合灯应为红（房产集中度）
    overall = limits_result.get("overall")
    print(f"{'✅' if overall == 'red' else '❌'} 综合灯: 实际={overall}, 预期=red")

    # 各分项灯
    for limit in limits_result.get("limits", []):
        print(f"  - {limit['name']}: {limit['status']} ({limit['display']})")

    print("\n" + "=" * 60)
    print("对账完成")
    print("=" * 60)


if __name__ == "__main__":
    test_reconciliation()
