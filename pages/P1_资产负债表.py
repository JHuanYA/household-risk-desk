"""
P1 资产负债表页面
展示资产负债明细，支持分类筛选
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def render_balance_sheet_page():
    """渲染资产负债表页面"""
    st.title("📋 资产负债表")
    st.markdown("**家庭资产负债明细与分类汇总**")
    st.markdown("---")

    if not st.session_state.get("data_loaded"):
        st.warning("请先在首页加载数据")
        return

    household = st.session_state.household
    metrics = st.session_state.baseline_metrics

    # 分类汇总
    cat_labels = {
        "cash": "现金及等价",
        "investment": "投资类",
        "property": "房产类",
        "other": "其他资产",
        "mortgage": "房贷",
        "consumer": "消费贷/卡债",
        "other_debt": "其他负债",
    }

    liab_labels = {
        "mortgage": "住宅按揭",
        "consumer": "信用卡/消费贷",
        "other_debt": "其他负债",
    }

    # 左侧：资产
    st.subheader("💰 资产")

    # 分类筛选
    asset_categories = ["全部", "现金", "投资", "房产", "其他"]
    selected_cat = st.selectbox("按类别筛选", asset_categories)

    assets = household[household["type"] == "asset"].copy()

    if selected_cat == "现金":
        assets = assets[assets["category"] == "cash"]
    elif selected_cat == "投资":
        assets = assets[assets["category"] == "investment"]
    elif selected_cat == "房产":
        assets = assets[assets["category"] == "property"]
    elif selected_cat == "其他":
        assets = assets[assets["category"] == "other"]

    # 流动性标记颜色
    liq_colors = {"high": "🟢", "medium": "🟡", "low": "🔴"}
    liq_labels = {"high": "高", "medium": "中", "low": "低"}

    # 资产明细表
    asset_display = assets[["name", "category", "amount", "currency", "hkd", "liquidity", "owner", "note"]].copy()
    asset_display.columns = ["名称", "类别", "原币金额", "币种", "港币金额", "流动性", "持有人", "备注"]
    asset_display["流动性"] = asset_display["流动性"].map(lambda x: f"{liq_colors.get(x, '')} {liq_labels.get(x, x)}")
    asset_display["类别"] = asset_display["类别"].map(lambda x: cat_labels.get(x, x))
    asset_display["原币金额"] = asset_display.apply(
        lambda r: f"{r['币种']} {r['原币金额']:,.0f}", axis=1
    )
    asset_display["港币金额"] = asset_display["港币金额"].apply(lambda x: f"HK${x:,.0f}")

    st.dataframe(asset_display, use_container_width=True, hide_index=True)

    # 资产分类汇总
    st.subheader("📊 资产分类汇总")

    cat_totals = metrics.get("catTotals", {})
    asset_summary = []
    for cat, amt in cat_totals.items():
        pct = amt / metrics.get("A", 1) * 100 if metrics.get("A", 0) > 0 else 0
        asset_summary.append({
            "类别": cat_labels.get(cat, cat),
            "金额 (HKD)": f"HK${amt:,.0f}",
            "占比": f"{pct:.1f}%",
        })

    if asset_summary:
        summary_df = pd.DataFrame(asset_summary)
        st.table(summary_df)

    # 资产合计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("资产合计", f"HK${metrics.get('A', 0):,.0f}")
    with col2:
        st.metric("高流动性资产", f"HK${metrics.get('A_high', 0):,.0f}")
    with col3:
        st.metric("流动性月数", f"{metrics.get('LIM', 0):.2f} 个月" if metrics.get('LIM') else "N/A")

    st.markdown("---")

    # 右侧：负债
    st.subheader("💳 负债")

    liabs = household[household["type"] == "liability"].copy()

    liab_display = liabs[["name", "category", "amount", "currency", "owner", "monthly_payment", "note"]].copy()
    liab_display.columns = ["名称", "类别", "余额", "币种", "持有人", "月供款", "备注"]
    liab_display["类别"] = liab_display["类别"].map(lambda x: liab_labels.get(x, x))
    liab_display["余额"] = liab_display.apply(
        lambda r: f"{r['币种']} {r['余额']:,.0f}", axis=1
    )
    liab_display["月供款"] = liab_display["月供款"].apply(
        lambda x: f"HK${x:,.0f}" if pd.notna(x) else "—"
    )

    st.dataframe(liab_display, use_container_width=True, hide_index=True)

    # 负债分类汇总
    st.subheader("📊 负债分类汇总")

    liab_summary = []
    for cat in liabs["category"].unique():
        cat_df = liabs[liabs["category"] == cat]
        amt = cat_df["hkd"].sum()
        pct = amt / metrics.get("L", 1) * 100 if metrics.get("L", 0) > 0 else 0
        liab_summary.append({
            "类别": liab_labels.get(cat, cat),
            "金额 (HKD)": f"HK${amt:,.0f}",
            "占比": f"{pct:.1f}%",
        })

    if liab_summary:
        summary_df = pd.DataFrame(liab_summary)
        st.table(summary_df)

    # 负债合计
    col1, col2 = st.columns(2)
    with col1:
        st.metric("负债合计", f"HK${metrics.get('L', 0):,.0f}")
    with col2:
        st.metric("净值", f"HK${metrics.get('E', 0):,.0f}")

    st.markdown("---")

    # 资产负债表可视化
    st.subheader("📈 资产负债结构")

    col_left, col_right = st.columns(2)

    with col_left:
        # 资产结构条形图
        if cat_totals:
            bar_data = pd.DataFrame([
                {"类别": cat_labels.get(cat, cat), "金额": amt, "类型": "资产"}
                for cat, amt in cat_totals.items()
            ])

            fig = px.bar(
                bar_data,
                x="类别",
                y="金额",
                color="类型",
                title="资产分类",
                color_discrete_map={"资产": "#2ecc71"},
            )
            fig.update_layout(showlegend=False)
            fig.update_yaxes(title="金额 (HKD)")
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        # 负债结构条形图
        if len(liab_summary) > 0:
            liab_bar_data = pd.DataFrame(liab_summary)
            liab_bar_data.columns = ["类别", "金额", "占比"]
            liab_bar_data["金额_num"] = liab_bar_data["金额"].str.replace("HK$", "").str.replace(",", "").astype(float)

            fig = px.bar(
                liab_bar_data,
                x="类别",
                y="金额_num",
                title="负债分类",
                color_discrete_map={"负债": "#e74c3c"},
            )
            fig.update_layout(showlegend=False)
            fig.update_yaxes(title="金额 (HKD)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无负债数据")

    st.markdown("---")

    # 流动性分析
    st.subheader("💧 流动性分析")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("高流动性资产", f"HK${metrics.get('A_high', 0):,.0f}")
    with col2:
        st.metric("中流动性资产", f"HK${metrics.get('A_invest', 0):,.0f}")
    with col3:
        st.metric("低流动性资产", f"HK${metrics.get('A_property', 0) + metrics.get('A_other', 0):,.0f}")
    with col4:
        lim = metrics.get("LIM")
        st.metric("流动性月数", f"{lim:.2f} 个月" if lim else "N/A")

    st.info("""
    **流动性分级说明**:
    - 🟢 高流动性：约 0-7 天可动用，如现金、活期、货币基金
    - 🟡 中流动性：可卖出但有价格波动，如股票、基金
    - 🔴 低流动性：变现慢或折价大，如房产、强积金
    """)


if __name__ == "__main__":
    render_balance_sheet_page()
