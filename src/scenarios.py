"""
压力情景模块
管理预置压力情景，支持情景对比分析
"""

import yaml
import os
from typing import Dict, Any, List, Optional

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "scenarios.yaml")


def load_scenarios() -> List[Dict[str, Any]]:
    """加载预置情景配置"""
    with open(SCENARIOS_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("scenarios", [])


def get_scenario_by_id(scenario_id: str) -> Optional[Dict[str, Any]]:
    """根据 ID 获取情景"""
    scenarios = load_scenarios()
    for sc in scenarios:
        if sc["id"] == scenario_id:
            return sc
    return None


def get_default_scenario() -> Optional[Dict[str, Any]]:
    """获取默认选中的情景"""
    scenarios = load_scenarios()
    for sc in scenarios:
        if sc.get("default", False):
            return sc
    # 如果没有默认，返回基准
    for sc in scenarios:
        if sc["id"] == "base":
            return sc
    return scenarios[0] if scenarios else None


def get_all_scenarios() -> List[Dict[str, Any]]:
    """获取全部情景"""
    return load_scenarios()


def compare_scenarios(
    baseline_metrics: Dict[str, Any],
    stress_metrics: Dict[str, Any],
    baseline_limits: Dict[str, Any],
    stress_limits: Dict[str, Any]
) -> Dict[str, Any]:
    """
    对比基准和压力情景

    Returns:
        包含对比数据和击穿清单
    """
    # 需要对比的指标
    compare_keys = [
        ("E", "净值", "HKD"),
        ("A", "资产", "HKD"),
        ("L", "负债", "HKD"),
        ("A_high", "高流动性资产", "HKD"),
        ("LIM", "流动性月数", "月"),
        ("GAP", "应急金缺口", "HKD"),
        ("LEV", "杠杆", "%"),
        ("DSTI", "DSTI", "%"),
    ]

    comparison = []
    breaches = []

    for key, name, unit in compare_keys:
        base_val = baseline_metrics.get(key)
        stress_val = stress_metrics.get(key)

        # 格式化值
        if unit == "HKD":
            base_display = f"HK${base_val:,.0f}" if base_val is not None else "N/A"
            stress_display = f"HK${stress_val:,.0f}" if stress_val is not None else "N/A"
            diff = (stress_val or 0) - (base_val or 0) if base_val is not None and stress_val is not None else None
            diff_display = f"HK${diff:+,.0f}" if diff is not None else "N/A"
        elif unit == "%":
            base_display = f"{base_val:.2%}" if base_val is not None else "N/A"
            stress_display = f"{stress_val:.2%}" if stress_val is not None else "N/A"
            diff = (stress_val or 0) - (base_val or 0) if base_val is not None and stress_val is not None else None
            diff_display = f"{diff:+.2%}" if diff is not None else "N/A"
        else:  # 月
            base_display = f"{base_val:.2f}" if base_val is not None else "N/A"
            stress_display = f"{stress_val:.2f}" if stress_val is not None else "N/A"
            diff = (stress_val or 0) - (base_val or 0) if base_val is not None and stress_val is not None else None
            diff_display = f"{diff:+.2f}" if diff is not None else "N/A"

        comparison.append({
            "key": key,
            "name": name,
            "unit": unit,
            "baseline": base_val,
            "baseline_display": base_display,
            "stress": stress_val,
            "stress_display": stress_display,
            "diff": diff,
            "diff_display": diff_display,
        })

    # 检查击穿项
    base_limits = baseline_limits.get("limits", [])
    stress_limits_list = stress_limits.get("limits", [])

    stress_limit_dict = {l["id"]: l for l in stress_limits_list}

    for base_limit in base_limits:
        limit_id = base_limit["id"]
        base_status = base_limit["status"]
        stress_limit = stress_limit_dict.get(limit_id)
        if stress_limit:
            stress_status = stress_limit["status"]

            # 红灯升级或新增红灯
            if stress_status == "red" and base_status != "red":
                breaches.append({
                    "id": limit_id,
                    "name": base_limit["name"],
                    "baseline_status": base_status,
                    "stress_status": stress_status,
                    "reason": stress_limit.get("reason", ""),
                })

    # 综合灯变化
    overall_base = baseline_limits.get("overall", "green")
    overall_stress = stress_limits.get("overall", "green")

    return {
        "comparison": comparison,
        "breaches": breaches,
        "overall_baseline": overall_base,
        "overall_stress": overall_stress,
        "overall_changed": overall_base != overall_stress,
    }


def generate_conclusion(
    scenario_name: str,
    comparison: Dict[str, Any],
    unemployment_data: Optional[Dict[str, Any]] = None
) -> str:
    """生成压力测试结论句"""
    conclusions = []

    # 综合灯变化
    if comparison["overall_changed"]:
        status_map = {"green": "绿", "yellow": "黄", "red": "红"}
        conclusions.append(
            f"{scenario_name}下综合灯由{status_map[comparison['overall_baseline']]}变{status_map[comparison['overall_stress']]}。"
        )
    else:
        conclusions.append(f"{scenario_name}下综合灯维持{comparison['overall_baseline']}。")

    # 击穿项
    if comparison["breaches"]:
        breach_names = [b["name"] for b in comparison["breaches"]]
        conclusions.append(f"击穿限额: {', '.join(breach_names)}。")

    # 失业情景专用
    if unemployment_data:
        gap6 = unemployment_data.get("gap6", 0)
        lim = unemployment_data.get("monthsCovered")
        if gap6 > 0:
            conclusions.append(f"6个月失业缺口约HK${gap6:,.0f}。")
        elif lim is not None:
            conclusions.append(f"现金可覆盖约{lim:.1f}个月。")

    return " ".join(conclusions) if conclusions else f"{scenario_name}情景下无显著风险变化。"
