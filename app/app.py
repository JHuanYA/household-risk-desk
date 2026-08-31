"""
家庭财务风险驾驶舱
Streamlit 应用入口
"""

import streamlit as st
import os

# 页面配置
st.set_page_config(
    page_title="家庭财务风险驾驶舱",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


# 初始化会话状态
def init_session_state():
    """初始化会话状态"""
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
        st.session_state.household = None
        st.session_state.cashflow = None
        st.session_state.fx_rates = None
        st.session_state.as_of = None
        st.session_state.baseline_metrics = None
        st.session_state.baseline_limits = None

    if "mode" not in st.session_state:
        st.session_state.mode = "demo"

    if "selected_scenario" not in st.session_state:
        default = get_default_scenario()
        st.session_state.selected_scenario = default["id"] if default else "base"


@st.cache_data
def load_data_cached(data_dir: str):
    """缓存数据加载"""
    return load_all_data(data_dir)


def load_data():
    """加载数据"""
    data_dir = get_data_dir(st.session_state.mode)
    household, cashflow, fx_df, fx_rates, as_of = load_data_cached(data_dir)

    # 计算基准指标
    baseline_metrics = compute_metrics(household, cashflow)
    baseline_limits = compute_all_limits(baseline_metrics)

    st.session_state.household = household
    st.session_state.cashflow = cashflow
    st.session_state.fx_rates = fx_rates
    st.session_state.as_of = as_of
    st.session_state.baseline_metrics = baseline_metrics
    st.session_state.baseline_limits = baseline_limits
    st.session_state.data_loaded = True


# 侧边栏
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title("🏠 家庭财务风险驾驶舱")

        # 模式切换
        st.session_state.mode = st.radio(
            "数据模式",
            options=["demo", "本地"],
            index=0 if st.session_state.mode == "demo" else 1,
            format_func=lambda x: "演示模式 (Demo)" if x == "demo" else "本地数据",
            help="切换使用演示数据或本地数据",
        )

        st.divider()

        # 数据信息
        if st.session_state.data_loaded:
            st.caption(f"**汇率日期**: {st.session_state.as_of}")
            st.caption(f"**数据模式**: {'Demo' if st.session_state.mode == 'demo' else '本地'}")
        else:
            st.info("点击首页加载数据")

        st.divider()

        # 综合灯显示
        if st.session_state.data_loaded:
            overall = st.session_state.baseline_limits.get("overall", "green")
            status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
            status_text = {"green": "良好", "yellow": "预警", "red": "危险"}
            st.metric(
                "综合风险状态",
                status_text.get(overall, "未知"),
                delta=status_icon.get(overall, "⚪"),
            )

        st.divider()

        # 导航说明
        st.caption("**页面导航**")
        st.caption("• 总览 - 风险全貌")
        st.caption("• 资产负债表 - 资产负债明细")
        st.caption("• 现金流 - 收支情况")
        st.caption("• 压力测试 - 情景分析")
        st.caption("• 限额假设 - 阈值配置")

        st.divider()

        # 免责声明
        st.caption(
            """
            ⚠️ **免责声明**  
            本工具不构成投资、信贷或税务建议。  
            数据仅供演示，请勿作为财务决策依据。
            """
        )


def main():
    """主函数"""
    init_session_state()

    # 加载数据
    try:
        load_data()
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        return

    # 渲染侧边栏
    render_sidebar()

    # 页面标题
    st.title("🏠 家庭财务风险驾驶舱")
    st.markdown("** Household Financial Risk Desk **")
    st.markdown("---")

    # 欢迎信息
    col1, col2 = st.columns([2, 1])

    with col1:
        st.success("✅ 数据加载成功")
        st.markdown(f"""
        ### 欢迎使用家庭财务风险驾驶舱

        本工具帮助您：
        - 📊 **看清家底**：资产、负债、净值一目了然
        - ⚠️ **识别风险**：流动性、杠杆、集中度多维监控
        - 🧪 **压力测试**：模拟失业、市场下跌等情景
        - 📋 **限额管理**：设定风险偏好，持续跟踪

        ---
        **数据模式**: {'🎭 Demo (演示数据)' if st.session_state.mode == 'demo' else '📁 本地数据'}  
        **汇率日期**: {st.session_state.as_of}
        """)

    with col2:
        overall = st.session_state.baseline_limits.get("overall", "green")
        status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        status_text = {"green": "良好", "yellow": "预警", "red": "危险"}

        st.metric(
            "综合风险状态",
            status_text.get(overall, "未知"),
            delta=status_icon.get(overall, "⚪"),
        )

        metrics = st.session_state.baseline_metrics
        st.metric("净值", f"HK${metrics.get('E', 0):,.0f}")
        st.metric("流动性月数", f"{metrics.get('LIM', 0):.2f} 个月" if metrics.get('LIM') else "N/A")

    st.markdown("---")
    st.info("👈 请使用左侧导航栏切换到各页面查看详情")


if __name__ == "__main__":
    main()
