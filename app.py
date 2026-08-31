"""
家庭财务风险驾驶舱
Streamlit 单页面应用入口 — 用 session_state.current_page 做 SPA 路由
所有导航和按钮都在同一页面内切换，不新开标签页
"""

import streamlit as st
import os
import sys

# ===== 页面配置（必须在第一个 st.* 调用前）=====
st.set_page_config(
    page_title="家庭财务风险驾驶舱",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 项目根目录
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from src import (
    load_all_data,
    get_data_dir,
    compute_metrics,
    compute_all_limits,
    get_default_scenario,
    get_all_scenarios,
    compare_scenarios,
    generate_conclusion,
)
from src.theme import inject_css, custom_sidebar, TOKEN, STATUS_MAP, _set_page

# ===== 注入全局 CSS（只执行一次）=====
inject_css()


# ===== 初始化 session_state =====
def init_session_state():
    defaults = {
        "data_loaded": False,
        "household": None,
        "cashflow": None,
        "fx_rates": None,
        "as_of": None,
        "baseline_metrics": None,
        "baseline_limits": None,
        "mode": "demo",
        "selected_scenario": None,
        "current_page": "overview",  # SPA 路由：overview / balance / cashflow / stress / limits
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if st.session_state.selected_scenario is None:
        default = get_default_scenario()
        st.session_state.selected_scenario = default["id"] if default else "base"


@st.cache_data
def load_data_cached(data_dir: str):
    return load_all_data(data_dir)


def load_data():
    data_dir = get_data_dir(st.session_state.mode)
    household, cashflow, fx_df, fx_rates, as_of = load_data_cached(data_dir)
    baseline_metrics = compute_metrics(household, cashflow)
    baseline_limits = compute_all_limits(baseline_metrics)
    st.session_state.household = household
    st.session_state.cashflow = cashflow
    st.session_state.fx_rates = fx_rates
    st.session_state.as_of = as_of
    st.session_state.baseline_metrics = baseline_metrics
    st.session_state.baseline_limits = baseline_limits
    st.session_state.data_loaded = True


def get_overall_status():
    """获取综合灯状态字符串"""
    if not st.session_state.get("data_loaded"):
        return "green"
    return st.session_state.baseline_limits.get("overall", "green")


def format_hkd(amount):
    """格式化港币"""
    if amount is None:
        return "N/A"
    return f"HK${amount:,.0f}"


# ===== 侧边栏页面配置（page_key 用于 session_state 路由）=====
# 注意：P0 导出 render_overview_page，P1-P4 都导出 render_page
# views/ 目录（原 pages/）作为普通 Python 模块，避免 Streamlit 自动子页面路由
PAGES = [
    {"label": "总览",         "icon": "📊", "page_key": "overview", "file": "views.P0_总览",     "func": "render_overview_page"},
    {"label": "资产负债表",   "icon": "📋", "page_key": "balance",  "file": "views.P1_资产负债表", "func": "render_page"},
    {"label": "现金流",       "icon": "💵", "page_key": "cashflow", "file": "views.P2_现金流",   "func": "render_page"},
    {"label": "压力测试",     "icon": "🧪", "page_key": "stress",   "file": "views.P3_压力测试", "func": "render_page"},
    {"label": "限额与假设",   "icon": "📐", "page_key": "limits",   "file": "views.P4_限额与假设", "func": "render_page"},
]


def render_sidebar():
    """渲染自定义侧边栏（导航按钮 + 数据模式卡 + 风险循环）"""
    current = st.session_state.get("current_page", "overview")
    pages_with_active = []
    for p in PAGES:
        pp = dict(p)
        pp["active"] = (current == p["page_key"])
        pages_with_active.append(pp)

    as_of = st.session_state.get("as_of", "")
    mode = st.session_state.get("mode", "demo")
    light = get_overall_status()
    custom_sidebar(mode, as_of, light, pages_with_active)


def dispatch_page():
    """根据 session_state.current_page 调用对应渲染函数"""
    current = st.session_state.get("current_page", "overview")
    for p in PAGES:
        if p["page_key"] == current:
            # 延迟导入，避免循环
            mod = __import__(p["file"], fromlist=[p["func"]])
            func = getattr(mod, p["func"])
            func()
            return
    # fallback → 总览
    mod = __import__("views.P0_总览", fromlist=["render_overview_page"])
    mod.render_overview_page()


# ===== 主入口 =====
def main():
    init_session_state()

    # 自动加载数据（首次 / 模式切换时）
    if not st.session_state.data_loaded:
        try:
            load_data()
        except Exception as e:
            st.error(f"数据加载失败: {str(e)}")
            return

    # 统一渲染侧边栏
    render_sidebar()

    # SPA 路由 → 渲染对应页面
    dispatch_page()


if __name__ == "__main__":
    main()
