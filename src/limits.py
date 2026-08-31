"""
限额与灯号模块
按照 PRD 第 8.3 章判断每条限额的状态
"""

import yaml
import os
from typing import Dict, Any, List, Optional

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIMITS_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "limits.yaml")


# 灯号等级
RANK = {"green": 0, "yellow": 1, "red": 2}


def worst(a: str, b: str) -> str:
    """取较差的灯号"""
    return a if RANK[a] >= RANK[b] else b


def load_limits_config() -> Dict[str, float]:
    """加载限额配置"""
    with open(LIMITS_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def check_lim(metrics: Dict[str, Any], config: Dict[str, float]) -> Dict[str, Any]:
    """流动性月数限额"""
    lim = metrics.get("LIM")
    lim_available = metrics.get("limAvailable", True)

    if not lim_available or lim is None:
        return {
            "id": "LIM",
            "name": "流动性月数",
            "value": None,
            "display": "不可用",
            "status": "red",
            "yellow": f"< {config['lim_target_months']}",
            "red": f"< {config['lim_red_below']}",
            "reason": "必要支出未录入，流动性指标不可用",
        }

    if lim < config["lim_red_below"]:
        status = "red"
    elif lim < config["lim_yellow_below"]:
        status = "yellow"
    else:
        status = "green"

    return {
        "id": "LIM",
        "name": "流动性月数",
        "value": lim,
        "display": f"{lim:.2f} 个月",
        "status": status,
        "yellow": f"< {config['lim_yellow_below']}",
        "red": f"< {config['lim_red_below']}",
        "reason": f"高流动性资产可覆盖 {lim:.2f} 个月必要支出，目标 {config['lim_target_months']} 个月",
    }


def check_lev(metrics: Dict[str, Any], config: Dict[str, float]) -> Dict[str, Any]:
    """杠杆限额"""
    lev = metrics.get("LEV")

    if not isinstance(lev, (int, float)) or lev == float("inf"):
        return {
            "id": "LEV",
            "name": "杠杆 L/A",
            "value": None,
            "display": "无穷大",
            "status": "red",
            "yellow": f"> {config['lev_yellow_above']:.0%}",
            "red": f"> {config['lev_red_above']:.0%}",
            "reason": "资产为零，杠杆无穷大",
        }

    if lev > config["lev_red_above"]:
        status = "red"
    elif lev > config["lev_yellow_above"]:
        status = "yellow"
    else:
        status = "green"

    return {
        "id": "LEV",
        "name": "杠杆 L/A",
        "value": lev,
        "display": f"{lev:.2%}",
        "status": status,
        "yellow": f"> {config['lev_yellow_above']:.0%}",
        "red": f"> {config['lev_red_above']:.0%}",
        "reason": f"负债占总资产 {lev:.2%}，超过阈值" if status != "green" else f"负债占总资产 {lev:.2%}",
    }


def check_equity(metrics: Dict[str, Any], config: Dict[str, float]) -> Dict[str, Any]:
    """净值限额"""
    e = metrics.get("E", 0)

    if e < 0:
        status = "red"
        reason = "净资产为负，已触发偿付危机定义"
    else:
        status = "green"
        reason = "净资产为正"

    return {
        "id": "E",
        "name": "净值",
        "value": e,
        "display": f"HK${e:,.0f}",
        "status": status,
        "yellow": "—",
        "red": "< 0",
        "reason": reason,
    }


def check_dsti(metrics: Dict[str, Any], config: Dict[str, float]) -> Dict[str, Any]:
    """偿债比率限额"""
    dsti = metrics.get("DSTI")
    inc = metrics.get("INC", 0)
    ds = metrics.get("DS", 0)

    if dsti is None:
        return {
            "id": "DSTI",
            "name": "偿债比率 DSTI",
            "value": None,
            "display": "不适用",
            "status": "green",
            "yellow": f"> {config['dsti_yellow_above']:.0%}",
            "red": f"> {config['dsti_red_above']:.0%}",
            "reason": "收入和债务供款均为零",
        }

    if not isinstance(dsti, (int, float)) or dsti == float("inf"):
        return {
            "id": "DSTI",
            "name": "偿债比率 DSTI",
            "value": None,
            "display": "不适用",
            "status": "red",
            "yellow": f"> {config['dsti_yellow_above']:.0%}",
            "red": f"> {config['dsti_red_above']:.0%}",
            "reason": "收入为零但仍有债务供款",
        }

    if dsti > config["dsti_red_above"]:
        status = "red"
    elif dsti > config["dsti_yellow_above"]:
        status = "yellow"
    else:
        status = "green"

    return {
        "id": "DSTI",
        "name": "偿债比率 DSTI",
        "value": dsti,
        "display": f"{dsti:.2%}",
        "status": status,
        "yellow": f"> {config['dsti_yellow_above']:.0%}",
        "red": f"> {config['dsti_red_above']:.0%}",
        "reason": f"月供款占收入 {dsti:.2%}，债务服务压力偏高" if status != "green" else f"月供款占收入 {dsti:.2%}",
    }


def check_invest(metrics: Dict[str, Any], config: Dict[str, float]) -> Dict[str, Any]:
    """投资集中度限额"""
    e = metrics.get("E", 0)
    invest_ratio = metrics.get("investRatio")

    if e <= 0:
        return {
            "id": "INVEST",
            "name": "投资 / 净值",
            "value": None,
            "display": "不适用",
            "status": "red",
            "yellow": f"> {config['invest_yellow_above']:.0%}",
            "red": f"> {config['invest_red_above']:.0%}",
            "reason": "净值不为正，集中度不输出百分比",
        }

    if invest_ratio is None:
        return {
            "id": "INVEST",
            "name": "投资 / 净值",
            "value": None,
            "display": "N/A",
            "status": "green",
            "yellow": f"> {config['invest_yellow_above']:.0%}",
            "red": f"> {config['invest_red_above']:.0%}",
            "reason": "无投资类资产",
        }

    if invest_ratio > config["invest_red_above"]:
        status = "red"
    elif invest_ratio > config["invest_yellow_above"]:
        status = "yellow"
    else:
        status = "green"

    return {
        "id": "INVEST",
        "name": "投资 / 净值",
        "value": invest_ratio,
        "display": f"{invest_ratio:.2%}",
        "status": status,
        "yellow": f"> {config['invest_yellow_above']:.0%}",
        "red": f"> {config['invest_red_above']:.0%}",
        "reason": f"投资类资产占净值 {invest_ratio:.2%}，市场下跌会显著侵蚀家底" if status != "green" else f"投资类资产占净值 {invest_ratio:.2%}",
    }


def check_concentration(metrics: Dict[str, Any], config: Dict[str, float]) -> Dict[str, Any]:
    """单一类别集中度限额"""
    e = metrics.get("E", 0)
    max_cat_ratio = metrics.get("maxCatRatio")
    max_cat = metrics.get("maxCat", "N/A")

    if e <= 0:
        return {
            "id": "CONC",
            "name": "单一类别 / 净值",
            "value": None,
            "display": "不适用",
            "status": "red",
            "yellow": f"> {config['concentration_yellow_above']:.0%}",
            "red": f"> {config['concentration_red_above']:.0%}",
            "reason": "净值不为正，集中度不输出百分比",
        }

    if max_cat_ratio is None:
        return {
            "id": "CONC",
            "name": "单一类别 / 净值",
            "value": None,
            "display": "N/A",
            "status": "green",
            "yellow": f"> {config['concentration_yellow_above']:.0%}",
            "red": f"> {config['concentration_red_above']:.0%}",
            "reason": "无明确最大类别",
        }

    if max_cat_ratio > config["concentration_red_above"]:
        status = "red"
    elif max_cat_ratio > config["concentration_yellow_above"]:
        status = "yellow"
    else:
        status = "green"

    return {
        "id": "CONC",
        "name": "单一类别 / 净值",
        "value": max_cat_ratio,
        "display": f"{max_cat_ratio:.2%}",
        "status": status,
        "yellow": f"> {config['concentration_yellow_above']:.0%}",
        "red": f"> {config['concentration_red_above']:.0%}",
        "reason": f"类别 {max_cat} 占净值 {max_cat_ratio:.2%}，风险过于集中" if status != "green" else f"类别 {max_cat} 占净值 {max_cat_ratio:.2%}",
    }


def check_income_vulnerability(metrics: Dict[str, Any], config: Dict[str, float]) -> Dict[str, Any]:
    """收入单一性限额"""
    income_sources = metrics.get("incomeSources", 0)
    lim = metrics.get("LIM")
    lim_available = metrics.get("limAvailable", True)

    if income_sources <= 1 and lim_available and lim is not None:
        if lim < 3:
            status = "red"
        elif lim < config["lim_target_months"]:
            status = "yellow"
        else:
            status = "green"
    else:
        status = "green"

    return {
        "id": "INCOME",
        "name": "收入单一性",
        "value": income_sources,
        "display": f"{income_sources} 条",
        "status": status,
        "yellow": "来源≤1 且 LIM<6",
        "red": "来源≤1 且 LIM<3",
        "reason": f"收入来源 {income_sources} 条且应急金不足，抗失业能力弱" if status != "green" else f"收入来源 {income_sources} 条",
    }


def compute_all_limits(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算全部限额状态

    Returns:
        包含 limits 列表、alerts 列表、overall 综合灯
    """
    config = load_limits_config()

    # 逐一检查各项限额
    lim_result = check_lim(metrics, config)
    lev_result = check_lev(metrics, config)
    equity_result = check_equity(metrics, config)
    dsti_result = check_dsti(metrics, config)
    invest_result = check_invest(metrics, config)
    conc_result = check_concentration(metrics, config)
    income_result = check_income_vulnerability(metrics, config)

    limits = [
        lim_result,
        lev_result,
        equity_result,
        dsti_result,
        invest_result,
        conc_result,
        income_result,
    ]

    # 综合灯 = 最差灯
    overall = "green"
    for limit in limits:
        overall = worst(overall, limit["status"])

    # 告警列表 = 非绿灯
    alerts = [l for l in limits if l["status"] != "green"]

    return {
        "limits": limits,
        "alerts": alerts,
        "overall": overall,
    }


def get_limit_display(limit: Dict[str, Any]) -> str:
    """获取限额的显示格式"""
    status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    return f"{status_icon.get(limit['status'], '⚪')} {limit['name']}: {limit['display']}"
