"""
P4 限额与假设页面
展示限额配置、阈值、当前值、状态和原因句
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import load_limits_config


def render_limits_page():
    """渲染限额与假设页面"""
    st.title("📐 限额与假设")
    st.markdown("**风险限额配置与假设说明**")
    st.markdown("---")

    if not st.session_state.get("data_loaded"):
        st.warning("请先在首页加载数据")
        return

    limits_result = st.session_state.baseline_limits
    config = load_limits_config()

    # 综合灯
    overall = limits_result.get("overall", "green")
    status_icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
    status_text = {"green": "良好", "yellow": "预警", "red": "危险"}

    st.metric("综合风险状态", status_text.get(overall, "未知"), delta=status_icon.get(overall, "⚪"))

    st.markdown("---")

    # 限额表
    st.subheader("📋 限额状态表")

    limits = limits_result.get("limits", [])

    if limits:
        table_data = []
        for limit in limits:
            status_icon_limit = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
            table_data.append({
                "指标": limit["name"],
                "当前值": limit["display"],
                "黄灯阈值": limit.get("yellow", "—"),
                "红灯阈值": limit.get("red", "—"),
                "状态": f"{status_icon_limit.get(limit['status'], '⚪')} {limit['status'].upper()}",
                "原因": limit.get("reason", ""),
            })

        table_df = pd.DataFrame(table_data)
        st.dataframe(table_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 限额配置详情
    st.subheader("⚙️ 限额配置")

    config_data = [
        ("流动性目标月数", f"{config.get('lim_target_months', 6)} 个月", "应急金覆盖目标"),
        ("流动性黄灯阈值", f"< {config.get('lim_yellow_below', 6)} 个月", "目标未达标"),
        ("流动性红灯阈值", f"< {config.get('lim_red_below', 3)} 个月", "硬限额突破"),
        ("杠杆黄灯阈值", f"> {config.get('lev_yellow_above', 0.4):.0%}", "杠杆偏高"),
        ("杠杆红灯阈值", f"> {config.get('lev_red_above', 0.6):.0%}", "杠杆过高"),
        ("DSTI 黄灯阈值", f"> {config.get('dsti_yellow_above', 0.4):.0%}", "偿债压力偏高"),
        ("DSTI 红灯阈值", f"> {config.get('dsti_red_above', 0.5):.0%}", "偿债压力过大"),
        ("投资/净值黄灯", f"> {config.get('invest_yellow_above', 0.6):.0%}", "投资集中"),
        ("投资/净值红灯", f"> {config.get('invest_red_above', 0.8):.0%}", "投资过度集中"),
        ("单一类别黄灯", f"> {config.get('concentration_yellow_above', 0.7):.0%}", "类别集中"),
        ("单一类别红灯", f"> {config.get('concentration_red_above', 0.9):.0%}", "类别过度集中"),
    ]

    config_df = pd.DataFrame(config_data, columns=["配置项", "阈值", "说明"])
    st.dataframe(config_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 风险事件定义
    st.subheader("⚠️ 风险事件定义")

    risk_events = [
        ("流动性断裂", "高流动性资产不足以覆盖未来 N 个月必要支出", "LIM < 目标月数"),
        ("偿付危机", "净资产 < 0，或压力后净资产 < 0", "E < 0"),
        ("收入中断脆弱", "主要收入来源 ≤ 1 且应急金低于限额", "收入单一 + LIM < 6"),
        ("集中度过高", "单一资产类别占净值比例超过限额", "类别占比 > 限额"),
        ("债务服务压力", "月供款 / 月收入超过限额", "DSTI > 限额"),
    ]

    events_df = pd.DataFrame(risk_events, columns=["风险事件", "定义", "触发条件"])
    st.dataframe(events_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 主要假设
    st.subheader("📌 主要假设与口径")

    assumptions = """
    **金额口径**
    - 所有金额先按汇率折算为港币（HKD）后再汇总
    - 汇率来源：`fx.csv`，由用户手工维护

    **流动性分级**
    - 🟢 高流动性（high）：约 0-7 天可动用，如现金、活期、货币基金
    - 🟡 中流动性（medium）：可卖出但有价格波动，如股票、基金
    - 🔴 低流动性（low）：变现慢或折价大，如房产、强积金
    - **应急金只承认 high 级别**

    **指标公式**
    - 净值 E = 资产 A - 负债 L
    - 杠杆 LEV = 负债 L / 资产 A
    - 流动性月数 LIM = 高流动性资产 / 必要支出
    - 应急金缺口 GAP = max(0, 目标月数 × 必要支出 - 高流动性资产)
    - DSTI = 债务供款 / 月收入

    **集中度**
    - 分母用净值 E，不用总资产 A
    - E ≤ 0 时，集中度不输出百分比，直接红灯

    **压力测试**
    - 冲击作用在内存副本，不改原始 CSV
    - 失业情景采用存量视角：只看 A_high 能覆盖几个月

    **免责声明**
    - 本工具不构成投资、信贷或税务建议
    - 压力测试的冲击系数是简化假设，不代表预测
    """

    st.markdown(assumptions)

    st.markdown("---")

    # 告警列表
    alerts = limits_result.get("alerts", [])
    if alerts:
        st.subheader("🚨 需要关注的限额")

        for alert in alerts:
            status_icon_alert = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
            st.warning(
                f"{status_icon_alert.get(alert['status'], '⚪')} **{alert['name']}**: "
                f"{alert['display']} | {alert['reason']}"
            )
    else:
        st.success("🟢 所有限额均在达标范围内")


if __name__ == "__main__":
    render_limits_page()
