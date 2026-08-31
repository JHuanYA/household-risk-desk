"""
P2 现金流页面
展示收支情况、必要/非必要支出、债务供款
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def render_cashflow_page():
    """渲染现金流页面"""
    st.title("💵 现金流")
    st.markdown("**收入、支出与月结余分析**")
    st.markdown("---")

    if not st.session_state.get("data_loaded"):
        st.warning("请先在首页加载数据")
        return

    cashflow = st.session_state.cashflow
    metrics = st.session_state.baseline_metrics

    # 必要支出警告
    if not metrics.get("limAvailable", True):
        st.warning("⚠️ 必要支出未录入，流动性指标不可用")

    # 顶部指标卡
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("月收入", f"HK${metrics.get('INC', 0):,.0f}")
    with col2:
        st.metric("必要支出", f"HK${metrics.get('EXP_ess', 0):,.0f}")
    with col3:
        st.metric("债务供款", f"HK${metrics.get('DS', 0):,.0f}")
    with col4:
        cf = metrics.get("CF", 0)
        cf_color = "normal" if cf >= 0 else "inverse"
        st.metric("月结余", f"HK${cf:,.0f}", delta_color=cf_color)

    st.markdown("---")

    # 收入部分
    st.subheader("💰 收入")

    income = cashflow[cashflow["direction"] == "in"].copy()

    income_display = income[["name", "monthly_amount", "currency", "hkd", "source_rank", "note"]].copy()
    income_display.columns = ["来源", "原币金额", "币种", "港币金额", "来源排序", "备注"]
    income_display["原币金额"] = income_display.apply(
        lambda r: f"{r['币种']} {r['原币金额']:,.0f}", axis=1
    )
    income_display["港币金额"] = income_display["港币金额"].apply(lambda x: f"HK${x:,.0f}")

    st.dataframe(income_display, use_container_width=True, hide_index=True)

    # 收入来源统计
    income_sources = metrics.get("incomeSources", 0)
    st.info(f"收入来源数: **{income_sources} 条**")

    st.markdown("---")

    # 支出部分
    st.subheader("💸 支出")

    # 必要 vs 非必要
    expenses = cashflow[cashflow["direction"] == "out"].copy()
    expenses["is_essential"] = expenses["essential"] == 1
    expenses["is_debt_service"] = expenses["debt_service"] == 1

    # 支出类型筛选
    expense_types = ["全部", "必要支出", "非必要支出", "债务供款"]
    selected_type = st.selectbox("按类型筛选", expense_types)

    filtered_expenses = expenses.copy()
    if selected_type == "必要支出":
        filtered_expenses = filtered_expenses[filtered_expenses["essential"] == 1]
    elif selected_type == "非必要支出":
        filtered_expenses = filtered_expenses[filtered_expenses["essential"] == 0]
    elif selected_type == "债务供款":
        filtered_expenses = filtered_expenses[filtered_expenses["debt_service"] == 1]

    expense_display = filtered_expenses[["name", "monthly_amount", "currency", "hkd", "essential", "debt_service", "note"]].copy()
    expense_display.columns = ["项目", "原币金额", "币种", "港币金额", "必要", "债务服务", "备注"]

    # 类型标记
    def type_mark(is_ess, is_ds):
        if is_ds:
            return "债务供款"
        elif is_ess:
            return "必要支出"
        else:
            return "非必要支出"

    expense_display["类型"] = expense_display.apply(
        lambda r: type_mark(r["必要"], r["债务服务"]), axis=1
    )
    expense_display["必要"] = expense_display["必要"].map({1: "是", 0: "否"})
    expense_display["债务服务"] = expense_display["债务服务"].map({1: "是", 0: "否"})
    expense_display["原币金额"] = expense_display.apply(
        lambda r: f"{r['币种']} {r['原币金额']:,.0f}", axis=1
    )
    expense_display["港币金额"] = expense_display["港币金额"].apply(lambda x: f"HK${x:,.0f}")

    st.dataframe(expense_display[["项目", "类型", "港币金额", "必要", "债务服务", "备注"]], use_container_width=True, hide_index=True)

    st.markdown("---")

    # 支出汇总
    st.subheader("📊 支出分类汇总")

    # 按类型汇总
    expense_summary = []

    exp_ess = metrics.get("EXP_ess", 0)
    exp_non_ess = metrics.get("EXP_all", 0) - exp_ess
    ds = metrics.get("DS", 0)

    expense_summary.append({"类别": "必要支出", "金额": exp_ess, "占比": f"{exp_ess/metrics.get('EXP_all',1)*100:.1f}%" if metrics.get('EXP_all', 0) > 0 else "0%"})
    expense_summary.append({"类别": "非必要支出", "金额": exp_non_ess, "占比": f"{exp_non_ess/metrics.get('EXP_all',1)*100:.1f}%" if metrics.get('EXP_all', 0) > 0 else "0%"})

    summary_df = pd.DataFrame(expense_summary)
    st.table(summary_df)

    # 债务供款汇总
    st.subheader("🏦 债务供款汇总")

    ds_items = expenses[expenses["debt_service"] == 1]
    if len(ds_items) > 0:
        ds_display = ds_items[["name", "monthly_amount", "currency", "hkd", "note"]].copy()
        ds_display.columns = ["项目", "原币金额", "币种", "港币金额", "备注"]
        ds_display["原币金额"] = ds_display.apply(
            lambda r: f"{r['币种']} {r['原币金额']:,.0f}", axis=1
        )
        ds_display["港币金额"] = ds_display["港币金额"].apply(lambda x: f"HK${x:,.0f}")

        st.dataframe(ds_display, use_container_width=True, hide_index=True)

        st.info(f"债务供款合计: **HK${metrics.get('DS', 0):,.0f}**")
    else:
        st.info("暂无债务供款数据")

    st.markdown("---")

    # 可视化
    st.subheader("📈 收支结构")

    col_left, col_right = st.columns(2)

    with col_left:
        # 收入支出对比
        labels = ["收入", "必要支出", "非必要支出", "债务供款"]
        values = [
            metrics.get("INC", 0),
            metrics.get("EXP_ess", 0) - metrics.get("DS", 0),  # 必要支出不含债务供款
            metrics.get("EXP_all", 0) - metrics.get("EXP_ess", 0),
            metrics.get("DS", 0),
        ]

        bar_data = pd.DataFrame({"类别": labels, "金额": values})

        colors = ["#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"]
        fig = px.bar(
            bar_data,
            x="类别",
            y="金额",
            title="收入支出对比",
            color="类别",
            color_discrete_map=dict(zip(labels, colors)),
        )
        fig.update_layout(showlegend=False)
        fig.update_yaxes(title="金额 (HKD)")
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # 支出结构饼图
        pie_labels = ["必要支出", "非必要支出", "债务供款"]
        pie_values = [
            metrics.get("EXP_ess", 0) - metrics.get("DS", 0),
            metrics.get("EXP_all", 0) - metrics.get("EXP_ess", 0),
            metrics.get("DS", 0),
        ]

        pie_data = pd.DataFrame({"类别": pie_labels, "金额": pie_values})

        fig = px.pie(
            pie_data,
            values="金额",
            names="类别",
            title="支出结构",
            hole=0.4,
            color="类别",
            color_discrete_map={
                "必要支出": "#e74c3c",
                "非必要支出": "#f39c12",
                "债务供款": "#9b59b6",
            },
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # DSTI 分析
    st.subheader("💳 偿债比率 (DSTI) 分析")

    dsti = metrics.get("DSTI")
    if dsti and dsti != float("inf"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("DSTI", f"{dsti:.2%}")
        with col2:
            st.metric("月收入", f"HK${metrics.get('INC', 0):,.0f}")
        with col3:
            st.metric("月供款", f"HK${metrics.get('DS', 0):,.0f}")

        if dsti > 0.5:
            st.error(f"🔴 DSTI {dsti:.1%} 过高，债务服务压力极大")
        elif dsti > 0.4:
            st.warning(f"🟡 DSTI {dsti:.1%} 偏高，需关注债务管理")
        else:
            st.success(f"🟢 DSTI {dsti:.1%} 在合理范围内")
    else:
        st.info("DSTI 不适用（收入为零）")


if __name__ == "__main__":
    render_cashflow_page()
