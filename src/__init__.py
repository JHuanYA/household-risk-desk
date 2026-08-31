"""
家庭财务风险驾驶舱 - 核心模块
"""

from .data_loader import load_all_data, get_data_dir, DataValidationError
from .metrics import compute_metrics, format_number, get_metrics_summary
from .limits import compute_all_limits, load_limits_config
from .scenarios import (
    load_scenarios,
    get_scenario_by_id,
    get_default_scenario,
    get_all_scenarios,
    compare_scenarios,
    generate_conclusion,
)

__all__ = [
    "load_all_data",
    "get_data_dir",
    "DataValidationError",
    "compute_metrics",
    "format_number",
    "get_metrics_summary",
    "compute_all_limits",
    "load_limits_config",
    "load_scenarios",
    "get_scenario_by_id",
    "get_default_scenario",
    "get_all_scenarios",
    "compare_scenarios",
    "generate_conclusion",
]
