"""
P3 压力测试页面
预置情景对比分析
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import (
    get_all_scenarios,
    get_default_scenario,
    compute_metrics,
    compute_all_limits,
    compare_scenarios,
    generate_conclusion,
)


def render_stress_test_page():
    """渲染压力测试页面"""
    st.title("🧪 压力测试")
    st.markdown("**模拟不同情景下的风险变化**")
    st.markdown("---")

    if not st.session_state.get("data_loaded"):
        st.warning("请先在首页加载数据")
        return

    household = st.session_state.household
    cashflow = st.session_state.cashflow
    baseline_metrics = st.session_state.baseline_metrics
    baseline_limits = st.session_state.baseline_limits

    # 获取所有情景
    scenarios = get_all_scenarios()

    # 情景选择
    st.subheader("📋 情景选择")

    col1, col2 = st.columns([2, 1])

    with col1:
        scenario_options = {sc["id"]: sc["name"] for sc in scenarios}
        scenario_descriptions = {sc["id"]: sc.get("description", "") for sc in scenarios}

        selected_id = st.selectbox(
            "选择压力情景",
            options=list(scenario_options.keys()),
            format_func=lambda x: f"{scenario_options[x]} - {scenario_descriptions[x]}",
            index=next(
                (i for i, sc in enumerate(scenarios) if sc.get("default", False)),
                0
            ),
        )

    selected_scenario = next((sc for sc in scenarios if sc["id"] == selected_id), None)

    # 冲击系数展示
    if selected_scenario:
        st.markdown("**冲击系数**")
        shock_cols = st.columns(6)
        shock_coeffs = [
            ("收入", selected_scenario.get("income_mult", 1.0)),
            ("必要支出", selected_scenario.get("essential_exp_mult", 1.0)),
            ("投资", selected_scenario.get("invest_mult", 1.0)),
            ("房产", selected_scenario.get("property_mult", 1.0)),
            ("供款", selected_scenario.get("debt_service_mult", 1.0)),
            ("负债", selected_scenario.get("liability_mult", 1.0)),
        ]
        for i, (name, val) in enumerate(shock_coeffs):
            with shock_cols[i]:
                st.metric(name, f"×{val:.1f}")

    st.markdown("---")

    # 计算压力情景指标
    if selected_scenario:
        shock = {
            "income_mult": selected_scenario.get("income_mult", 1.0),
            "essential_exp_mult": selected_scenario.get("essential_exp_mult", 1.0),
            "invest_mult": selected_scenario.get("invest_mult", 1.0),
            "property_mult": selected_scenario.get("property_mult", 1.0),
            "debt_service_mult": selected_scenario.get("debt_service_mult", 1.0),
            "liability_mult": selected_scenario.get("liability_mult", 1.0),
        }

        stress_metrics = compute_metrics(household, cashflow, shock)
        stress_limits = compute_all_limits(stress_metrics)

        # 基准 vs 压力对比
        comparison = compare_scenarios(baseline_metrics, stress_metrics, baseline_limits, stress_limits)

        # 综合灯对比
        st.subheader("🚦 综合风险状态对比")

        col1, col2 = st.columns(2)
        status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        status_text = {"green": "良好", "yellow": "预警", "red": "危险"}

        with col1:
            overall_base = baseline_limits.get("overall", "green")
            st.metric(
                "基准综合灯",
                status_text.get(overall_base, "未知"),
                delta=status_icon.get(overall_base, "⚪"),
            )

        with col2:
            overall_stress = stress_limits.get("overall", "green")
            change_indicator = "↓" if comparison["overall_changed"] else "→"
            st.metric(
                f"压力情景综合灯 {change_indicator}",
                status_text.get(overall_stress, "未知"),
                delta=status_icon.get(overall_stress, "⚪"),
            )

        st.markdown("---")

        # 指标对照表
        st.subheader("📊 指标对照表")

        comparison_data = []
        for item in comparison["comparison"]:
            comparison_data.append({
                "指标": item["name"],
                "基准": item["baseline_display"],
                selected_scenario["name"]: item["stress_display"],
                "变化": item["diff_display"],
            })

        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # 击穿清单
        if comparison["breaches"]:
            st.subheader("⚠️ 击穿限额")

            for breach in comparison["breaches"]:
                st.error(
                    f"🔴 **{breach['name']}**: {breach['reason']} "
                    f"(基准:{breach['baseline_status']} → 压力:{breach['stress_status']})"
                )
        else:
            st.success("🟢 该情景下无限额被击穿")

        st.markdown("---")

        # 失业情景专用输出
        if shock.get("income_mult", 1.0) == 0:
            st.subheader("🏦 失业情景分析")

            unemployment = stress_metrics.get("unemployment", {})

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                need3 = unemployment.get("need3", 0)
                st.metric("3个月所需现金", f"HK${need3:,.0f}")
            with col2:
                gap3 = unemployment.get("gap3", 0)
                st.metric("3个月缺口", f"HK${gap3:,.0f}" if gap3 > 0 else "无缺口")
            with col3:
                need6 = unemployment.get("need6", 0)
                st.metric("6个月所需现金", f"HK${need6:,.0f}")
            with col4:
                gap6 = unemployment.get("gap6", 0)
                st.metric("6个月缺口", f"HK${gap6:,.0f}" if gap6 > 0 else "无缺口")

            lim = unemployment.get("monthsCovered")
            if lim is not None:
                if lim < 6:
                    st.warning(f"🟡 当前现金可覆盖约 {lim:.1f} 个月，低于 6 个月目标")
                else:
                    st.success(f"🟢 当前现金可覆盖约 {lim:.1f} 个月，达到目标")

        st.markdown("---")

        # 结论句
        st.subheader("📝 结论")

        conclusion = generate_conclusion(
            selected_scenario["name"],
            comparison,
            stress_metrics.get("unemployment"),
        )
        st.info(f"**{conclusion}**")

    st.markdown("---")

    # 全部情景概览
    st.subheader("📋 全部情景概览")

    overview_data = []
    for sc in scenarios:
        shock = {
            "income_mult": sc.get("income_mult", 1.0),
            "essential_exp_mult": sc.get("essential_exp_mult", 1.0),
            "invest_mult": sc.get("invest_mult", 1.0),
            "property_mult": sc.get("property_mult", 1.0),
            "debt_service_mult": sc.get("debt_service_mult", 1.0),
            "liability_mult": sc.get("liability_mult", 1.0),
        }

        sc_metrics = compute_metrics(household, cashflow, shock)
        sc_limits = compute_all_limits(sc_metrics)

        overview_data.append({
            "情景": sc["name"],
            "综合灯": status_icon.get(sc_limits.get("overall", "green"), "⚪"),
            "流动性月数": f"{sc_metrics.get('LIM', 0):.2f}" if sc_metrics.get('LIM') else "N/A",
            "杠杆": f"{sc_metrics.get('LEV', 0):.1%}" if sc_metrics.get('LEV') and sc_metrics.get('LEV') != float('inf') else "∞",
            "净值": f"HK${sc_metrics.get('E', 0):,.0f}",
            "应急金缺口": f"HK${sc_metrics.get('GAP', 0):,.0f}" if sc_metrics.get('GAP') else "N/A",
        })

    overview_df = pd.DataFrame(overview_data)
    st.dataframe(overview_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render_stress_test_page()
