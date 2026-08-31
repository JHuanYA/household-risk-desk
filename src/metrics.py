"""
指标计算引擎
按照 PRD 第 8 章公式计算所有风险指标
"""

import pandas as pd
from typing import Dict, Any, Optional, Tuple
from copy import deepcopy


def compute_metrics(
    household: pd.DataFrame,
    cashflow: pd.DataFrame,
    shock: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    计算全部风险指标

    Args:
        household: 资产负债 DataFrame
        cashflow: 现金流 DataFrame
        shock: 压力冲击系数

    Returns:
        包含所有指标的字典
    """
    shock = shock or {}

    # 提取冲击系数
    income_mult = shock.get("income_mult", 1.0)
    essential_exp_mult = shock.get("essential_exp_mult", 1.0)
    invest_mult = shock.get("invest_mult", 1.0)
    property_mult = shock.get("property_mult", 1.0)
    debt_service_mult = shock.get("debt_service_mult", 1.0)
    liability_mult = shock.get("liability_mult", 1.0)

    # 分离资产和负债
    assets = household[household["type"] == "asset"].copy()
    liabs = household[household["type"] == "liability"].copy()

    # 计算资产 HKD（应用冲击）
    def asset_hkd(row: pd.Series) -> float:
        if row["category"] == "investment":
            return row["hkd"] * invest_mult
        elif row["category"] == "property":
            return row["hkd"] * property_mult
        return row["hkd"]

    # 基础量
    A = assets.apply(asset_hkd, axis=1).sum()  # 资产合计
    L = (liabs["hkd"] * liability_mult).sum()  # 负债合计
    E = A - L  # 净值

    # 高流动性资产
    A_high = assets[assets["liquidity"] == "high"]["hkd"].sum()

    # 投资类资产
    A_invest = assets[assets["category"] == "investment"].apply(asset_hkd, axis=1).sum()

    # 房产类资产
    A_property = assets[assets["category"] == "property"].apply(asset_hkd, axis=1).sum()

    # 现金类资产
    A_cash = assets[assets["category"] == "cash"]["hkd"].sum()

    # 其他资产
    A_other = assets[assets["category"] == "other"]["hkd"].sum()

    # 分类汇总
    cat_totals = {}
    for cat in assets["category"].unique():
        cat_df = assets[assets["category"] == cat]
        cat_totals[cat] = cat_df.apply(asset_hkd, axis=1).sum()

    # 找最大类别
    max_cat = max(cat_totals, key=cat_totals.get) if cat_totals else None
    max_cat_amt = cat_totals.get(max_cat, 0) if max_cat else 0

    # 现金流计算
    # 月收入
    INC = cashflow[cashflow["direction"] == "in"].apply(
        lambda row: row["hkd"] * income_mult, axis=1
    ).sum()

    # 必要支出 (essential=1 的流出)
    def calc_ess_exp(row: pd.Series) -> float:
        if row["direction"] == "out" and row.get("essential", 0) == 1:
            mult = debt_service_mult * essential_exp_mult if row.get("debt_service", 0) == 1 else essential_exp_mult
            return row["hkd"] * mult
        return 0

    EXP_ess = cashflow.apply(calc_ess_exp, axis=1).sum()

    # 债务供款 (debt_service=1 的流出)
    def calc_ds(row: pd.Series) -> float:
        if row["direction"] == "out" and row.get("debt_service", 0) == 1:
            return row["hkd"] * debt_service_mult
        return 0

    DS = cashflow.apply(calc_ds, axis=1).sum()

    # 全部流出
    def calc_all_exp(row: pd.Series) -> float:
        if row["direction"] != "out":
            return 0
        if row.get("debt_service", 0) == 1:
            mult = debt_service_mult * (essential_exp_mult if row.get("essential", 0) == 1 else 1)
            return row["hkd"] * mult
        if row.get("essential", 0) == 1:
            return row["hkd"] * essential_exp_mult
        return row["hkd"]

    EXP_all = cashflow.apply(calc_all_exp, axis=1).sum()

    # 收入来源数
    income_sources_df = cashflow[
        (cashflow["direction"] == "in") &
        (cashflow["hkd"] * income_mult > 0) &
        (cashflow["source_rank"].notna())
    ]
    income_sources = income_sources_df["source_rank"].nunique()

    # 核心风险指标
    # 流动性月数
    lim_available = EXP_ess > 0
    LIM = A_high / EXP_ess if lim_available else None

    # 流动性天数
    LID = LIM * 30 if LIM is not None else None

    # 应急金缺口 (目标 6 个月)
    LIM_TARGET = 6
    GAP = max(0, LIM_TARGET * EXP_ess - A_high) if lim_available else None

    # 杠杆
    LEV = L / A if A > 0 else float("inf")

    # 偿债比率
    if INC > 0:
        DSTI = DS / INC
    elif DS > 0:
        DSTI = float("inf")
    else:
        DSTI = None

    # 集中度（分母用净值 E）
    def safe_ratio(numerator: float, denominator: float) -> Optional[float]:
        if denominator <= 0:
            return None
        return numerator / denominator

    invest_ratio = safe_ratio(A_invest, E)
    property_ratio = safe_ratio(A_property, E)
    max_cat_ratio = safe_ratio(max_cat_amt, E)

    # 月结余
    CF = INC - EXP_all

    # 组装结果
    result = {
        # 基础量
        "A": A,
        "L": L,
        "E": E,
        "A_high": A_high,
        "A_cash": A_cash,
        "A_invest": A_invest,
        "A_property": A_property,
        "A_other": A_other,
        "maxCat": max_cat,
        "maxCatAmt": max_cat_amt,
        # 现金流
        "INC": INC,
        "EXP_ess": EXP_ess,
        "EXP_all": EXP_all,
        "DS": DS,
        "CF": CF,
        "incomeSources": income_sources,
        # 风险指标
        "LIM": LIM,
        "LID": LID,
        "GAP": GAP,
        "LEV": LEV,
        "DSTI": DSTI,
        "investRatio": invest_ratio,
        "propertyRatio": property_ratio,
        "maxCatRatio": max_cat_ratio,
        # 辅助
        "limAvailable": lim_available,
        "catTotals": cat_totals,
    }

    # 失业情景专用输出
    if income_mult == 0:
        result["unemployment"] = {
            "need3": EXP_ess * 3,
            "need6": EXP_ess * 6,
            "gap3": max(0, EXP_ess * 3 - A_high),
            "gap6": max(0, EXP_ess * 6 - A_high),
            "monthsCovered": LIM,
        }

    return result


def format_number(n: Optional[float], unit: str = "", decimals: int = 0) -> str:
    """格式化数字显示"""
    if n is None:
        return "N/A"
    if unit == "%":
        return f"{n * 100:.1f}%" if isinstance(n, float) else "N/A"
    if unit == "月":
        return f"{n:.2f} 个月" if isinstance(n, float) else "N/A"
    # 金额格式
    return f"HK${n:,.0f}"


def get_metrics_summary(metrics: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """获取指标摘要，用于展示"""
    return {
        "净值 E": {
            "value": metrics.get("E"),
            "unit": "HKD",
            "display": format_number(metrics.get("E"), "HKD"),
        },
        "杠杆 L/A": {
            "value": metrics.get("LEV"),
            "unit": "%",
            "display": format_number(metrics.get("LEV"), "%"),
        },
        "流动性月数": {
            "value": metrics.get("LIM"),
            "unit": "月",
            "display": format_number(metrics.get("LIM"), "月"),
        },
        "应急金缺口": {
            "value": metrics.get("GAP"),
            "unit": "HKD",
            "display": format_number(metrics.get("GAP"), "HKD"),
        },
        "DSTI": {
            "value": metrics.get("DSTI"),
            "unit": "%",
            "display": format_number(metrics.get("DSTI"), "%"),
        },
    }
