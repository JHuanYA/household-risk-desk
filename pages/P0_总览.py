"""
P0 总览页面
30秒判断家庭风险态势
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def render_overview_page():
    """渲染总览页面"""
    st.title("📊 总览")
    st.markdown("**30秒判断家庭风险态势**")
    st.markdown("---")

    if not st.session_state.get("data_loaded"):
        st.warning("请先在首页加载数据")
        return

    metrics = st.session_state.baseline_metrics
    limits_result = st.session_state.baseline_limits

    # 综合灯
    overall = limits_result.get("overall", "green")
    status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    status_text = {"green": "良好", "yellow": "预警", "red": "危险"}

    # 指标卡片行
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "综合风险",
            status_text.get(overall, "未知"),
            delta=status_icon.get(overall, "⚪"),
        )

    with col2:
        e = metrics.get("E", 0)
        st.metric("净值", f"HK${e:,.0f}")

    with col3:
        lev = metrics.get("LEV")
        lev_display = f"{lev:.2%}" if lev and lev != float("inf") else "无穷大"
        lev_status = limits_result.get("limits", [{}])[1]  # LEV 是第二个
        st.metric("杠杆 L/A", lev_display)

    with col4:
        lim = metrics.get("LIM")
        lim_display = f"{lim:.2f} 个月" if lim else "N/A"
        st.metric("流动性月数", lim_display)

    with col5:
        gap = metrics.get("GAP")
        gap_display = f"HK${gap:,.0f}" if gap else "N/A"
        st.metric("应急金缺口", gap_display)

    st.markdown("---")

    # 告警列表
    alerts = limits_result.get("alerts", [])
    if alerts:
        st.subheader("⚠️ 风险告警")

        for alert in alerts:
            status_icon_alert = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
            st.warning(
                f"{status_icon_alert.get(alert['status'], '⚪')} **{alert['name']}**: {alert['display']} | {alert['reason']}"
            )
    else:
        st.success("🟢 所有风险指标均在限额内")

    st.markdown("---")

    # 资产结构 + 指标详情
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📊 资产结构")

        # 资产结构饼图
        cat_labels = {
            "cash": "现金类",
            "investment": "投资类",
            "property": "房产类",
            "other": "其他资产",
        }

        cat_totals = metrics.get("catTotals", {})
        if cat_totals:
            pie_data = pd.DataFrame([
                {"类别": cat_labels.get(cat, cat), "金额": amt}
                for cat, amt in cat_totals.items()
            ])

            fig = px.pie(
                pie_data,
                values="金额",
                names="类别",
                title="资产分布",
                hole=0.4,
                color="类别",
                color_discrete_map={
                    "现金类": "#2ecc71",
                    "投资类": "#3498db",
                    "房产类": "#e74c3c",
                    "其他资产": "#95a5a6",
                },
            )
            fig.update_layout(
                font=dict(size=12),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无资产数据")

    with col_right:
        st.subheader("📋 核心指标详情")

        # 指标表格
        metrics_data = []

        # 资产
        metrics_data.append(("资产合计", f"HK${metrics.get('A', 0):,.0f}", ""))
        metrics_data.append(("高流动性资产", f"HK${metrics.get('A_high', 0):,.0f}", "应急金主体"))

        # 负债
        metrics_data.append(("负债合计", f"HK${metrics.get('L', 0):,.0f}", ""))

        # 净值
        metrics_data.append(("净值", f"HK${metrics.get('E', 0):,.0f}", ""))

        # 现金流
        metrics_data.append(("月收入", f"HK${metrics.get('INC', 0):,.0f}", ""))
        metrics_data.append(("必要支出", f"HK${metrics.get('EXP_ess', 0):,.0f}", ""))
        metrics_data.append(("债务供款", f"HK${metrics.get('DS', 0):,.0f}", ""))
        metrics_data.append(("月结余", f"HK${metrics.get('CF', 0):,.0f}", ""))

        # 风险指标
        metrics_data.append(("流动性月数", f"{metrics.get('LIM', 0):.2f} 个月" if metrics.get('LIM') else "N/A", ""))
        metrics_data.append(("应急金缺口", f"HK${metrics.get('GAP', 0):,.0f}" if metrics.get('GAP') else "N/A", ""))
        metrics_data.append(("杠杆 L/A", f"{metrics.get('LEV', 0):.2%}" if metrics.get('LEV') and metrics.get('LEV') != float('inf') else "无穷大", ""))
        metrics_data.append(("DSTI", f"{metrics.get('DSTI', 0):.2%}" if metrics.get('DSTI') else "N/A", ""))

        metrics_df = pd.DataFrame(metrics_data, columns=["指标", "数值", "备注"])
        st.table(metrics_df)

    st.markdown("---")

    # 态势句
    st.subheader("📝 风险态势总结")

    # 生成态势句
    situation_parts = []

    # 综合状态
    if overall == "red":
        situation_parts.append("综合风险状态为**红灯**，存在重大风险敞口。")
    elif overall == "yellow":
        situation_parts.append("综合风险状态为**黄灯**，需关注风险变化。")
    else:
        situation_parts.append("综合风险状态为**绿灯**，各项指标均在限额内。")

    # 流动性
    lim = metrics.get("LIM")
    if lim:
        if lim < 3:
            situation_parts.append(f"流动性严重不足，仅能覆盖{lim:.1f}个月，面临流动性断裂风险。")
        elif lim < 6:
            situation_parts.append(f"流动性偏低，可覆盖{lim:.1f}个月，低于6个月目标。")

    # 杠杆
    lev = metrics.get("LEV")
    if lev and lev != float("inf"):
        if lev > 0.6:
            situation_parts.append(f"杠杆率过高({lev:.1%})，偿债压力较大。")
        elif lev > 0.4:
            situation_parts.append(f"杠杆率偏高({lev:.1%})，需关注债务管理。")

    # 房产集中度
    prop_ratio = metrics.get("propertyRatio")
    if prop_ratio:
        if prop_ratio > 0.9:
            situation_parts.append(f"房产占净值{prop_ratio:.1%}，集中度过高，房价波动风险大。")
        elif prop_ratio > 0.6:
            situation_parts.append(f"房产占净值{prop_ratio:.1%}，房产风险敞口较大。")

    # 收入单一性
    income_sources = metrics.get("incomeSources", 0)
    if income_sources == 1:
        situation_parts.append("收入来源单一，抗失业风险能力弱。")

    # DSTI
    dsti = metrics.get("DSTI")
    if dsti:
        if dsti > 0.5:
            situation_parts.append(f"DSTI {dsti:.1%}，债务服务压力极大。")
        elif dsti > 0.4:
            situation_parts.append(f"DSTI {dsti:.1%}，债务服务压力偏高。")

    st.info(" ".join(situation_parts) if situation_parts else "数据加载中...")


if __name__ == "__main__":
    render_overview_page()
