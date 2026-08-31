"""
数据加载模块
负责读取 CSV 文件、校验数据、币种转换
"""

import pandas as pd
import os
from typing import Tuple, List, Dict, Optional

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "demo")


class DataValidationError(Exception):
    """数据校验异常"""
    pass


def load_household(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """加载资产负债表"""
    filepath = os.path.join(data_dir, "household.csv")
    df = pd.read_csv(filepath)

    # 必填字段校验
    required = ["item_id", "name", "type", "category", "amount", "currency"]
    for field in required:
        if field not in df.columns:
            raise DataValidationError(f"缺少必填字段: {field}")

    # type 校验
    valid_types = ["asset", "liability"]
    if not df["type"].isin(valid_types).all():
        invalid = df[~df["type"].isin(valid_types)]["item_id"].tolist()
        raise DataValidationError(f"type 字段无效: {invalid}")

    # amount 必须是数字
    if not pd.api.types.is_numeric_dtype(df["amount"]):
        raise DataValidationError("amount 必须是数字")

    # asset 必须有 liquidity
    assets = df[df["type"] == "asset"]
    if assets["liquidity"].isna().any():
        invalid = assets[assets["liquidity"].isna()]["item_id"].tolist()
        raise DataValidationError(f"资产缺少 liquidity 标记: {invalid}")

    # currency 校验
    valid_currencies = ["HKD", "USD", "CNY"]
    if not df["currency"].isin(valid_currencies).all():
        invalid = df[~df["currency"].isin(valid_currencies)]["item_id"].tolist()
        raise DataValidationError(f"currency 无效: {invalid}")

    return df


def load_cashflow(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """加载现金流表"""
    filepath = os.path.join(data_dir, "cashflow.csv")
    df = pd.read_csv(filepath)

    # 必填字段校验
    required = ["item_id", "name", "direction", "monthly_amount", "currency"]
    for field in required:
        if field not in df.columns:
            raise DataValidationError(f"缺少必填字段: {field}")

    # direction 校验
    valid_directions = ["in", "out"]
    if not df["direction"].isin(valid_directions).all():
        invalid = df[~df["direction"].isin(valid_directions)]["item_id"].tolist()
        raise DataValidationError(f"direction 字段无效: {invalid}")

    # monthly_amount 必须是数字
    if not pd.api.types.is_numeric_dtype(df["monthly_amount"]):
        raise DataValidationError("monthly_amount 必须是数字")

    # essential 和 debt_service 校验
    for field in ["essential", "debt_service"]:
        if field in df.columns:
            if not df[field].isin([0, 1]).all():
                invalid = df[~df[field].isin([0, 1])]["item_id"].tolist()
                raise DataValidationError(f"{field} 字段必须是 0 或 1: {invalid}")

    return df


def load_fx(data_dir: str = DATA_DIR) -> pd.DataFrame:
    """加载汇率表"""
    filepath = os.path.join(data_dir, "fx.csv")
    df = pd.read_csv(filepath)

    # 必填字段校验
    required = ["currency", "hkd_per_unit"]
    for field in required:
        if field not in df.columns:
            raise DataValidationError(f"缺少必填字段: {field}")

    # hkd_per_unit 必须是数字
    if not pd.api.types.is_numeric_dtype(df["hkd_per_unit"]):
        raise DataValidationError("hkd_per_unit 必须是数字")

    # 构建汇率字典
    fx_rates = {}
    for _, row in df.iterrows():
        fx_rates[row["currency"]] = row["hkd_per_unit"]
    fx_rates["HKD"] = 1.0  # HKD 默认 1

    as_of = df["as_of"].iloc[0] if "as_of" in df.columns else None

    return df, fx_rates, as_of


def validate_fx_coverage(household: pd.DataFrame, fx_rates: Dict[str, float]) -> List[str]:
    """校验汇率是否覆盖所有币种"""
    errors = []
    currencies = household["currency"].unique()
    for curr in currencies:
        if curr not in fx_rates:
            errors.append(f"缺少汇率: {curr}")
    return errors


def to_hkd(amount: float, currency: str, fx_rates: Dict[str, float]) -> float:
    """将金额转换为港币"""
    if currency not in fx_rates:
        raise DataValidationError(f"缺少汇率: {currency}")
    return amount * fx_rates[currency]


def load_all_data(data_dir: str = DATA_DIR) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, float], str]:
    """
    加载全部数据并进行校验

    Returns:
        (household, cashflow, fx_df, fx_rates, as_of)
    """
    errors = []

    # 加载数据
    try:
        household = load_household(data_dir)
        cashflow = load_cashflow(data_dir)
        fx_df, fx_rates, as_of = load_fx(data_dir)
    except FileNotFoundError as e:
        raise DataValidationError(f"数据文件未找到: {e}")

    # 校验汇率覆盖
    fx_errors = validate_fx_coverage(household, fx_rates)
    errors.extend(fx_errors)

    if errors:
        raise DataValidationError("; ".join(errors))

    # 添加 HKD 列
    household["hkd"] = household.apply(
        lambda row: to_hkd(row["amount"], row["currency"], fx_rates), axis=1
    )
    cashflow["hkd"] = cashflow.apply(
        lambda row: to_hkd(row["monthly_amount"], row["currency"], fx_rates), axis=1
    )

    return household, cashflow, fx_df, fx_rates, as_of


def get_data_dir(mode: str = "demo") -> str:
    """获取数据目录"""
    if mode == "demo":
        return os.path.join(PROJECT_ROOT, "data", "demo")
    else:
        return os.path.join(PROJECT_ROOT, "data", "local")
