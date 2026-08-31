"""
P1 资产负债表页
资产、负债、币种和流动性标记统一在一个视图下完成核对
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.theme import (
    metric_card, sub_card, section_title, pill,
    dark_plotly_layout, TOKEN, STATUS_MAP, _set_page,
)


def hkd(v):
    if v is None:
        return "—"
    return f"HK${v:,.0f}"


def hkd_short(v):
    if v is None:
        return "—"
    if abs(v) >= 1_000_000:
        return f"HK${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"HK${v/1_000:.0f}K"
    return f"HK${v:,.0f}"


def render_page():
    household = st.session_state.household
    metrics = st.session_state.baseline_metrics
    as_of = st.session_state.get("as_of", "")

    cat_labels = {
        "cash": "现金及等价", "investment": "投资", "property": "房产",
        "other": "其他资产", "mortgage": "房贷", "consumer": "消费贷/卡债",
        "other_debt": "其他负债",
    }
    liq_labels = {"high": "high", "medium": "medium", "low": "low"}
    liq_pretty = {"high": "高", "medium": "中", "low": "低"}
    liq_colors = {"high": TOKEN["green"], "medium": TOKEN["yellow"], "low": TOKEN["red"]}

    # ---------- 1. Header ----------
    header_html = f"""
    <div class="hf-header">
        <div>
            <h1 class="hf-header-title">资产负债表</h1>
            <p class="hf-header-sub">资产、负债、币种和流动性标记统一在一个视图下完成核对。</p>
        </div>
        <div class="hf-header-right">
            <div class="hf-header-chip">汇率日期 <br><b>{as_of}</b></div>
            <div class="hf-header-chip"><span class="hf-pill hf-pill-{st.session_state.baseline_limits.get('overall','green')}">
                {STATUS_MAP.get(st.session_state.baseline_limits.get('overall','green'), STATUS_MAP['green'])[0]}</span></div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    _col_back, _col_fill = st.columns([1, 9])
    with _col_back:
        st.button("重算并返回总览 →", key="balance_btn_overview",
                  on_click=_set_page, args=("overview",), use_container_width=True)

    # ---------- 2. 四张顶部卡片 ----------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("总资产", hkd_short(metrics.get("A", 0)), "房产与投资占主要权重", "neutral")
    with col2:
        metric_card("总负债", hkd_short(metrics.get("L", 0)), "房贷是主要负债来源", "warn")
    with col3:
        metric_card("净值", hkd_short(metrics.get("E", 0)), "压力后净值仍需持续跟踪", "neutral")
    with col4:
        max_cat = metrics.get("maxCat", "—")
        max_pct = metrics.get("maxCatRatio")
        pct_display = f"{max_pct:.0%}" if max_pct else "—"
        metric_card("最大类别集中度", pct_display, f"{cat_labels.get(max_cat, max_cat) if max_cat and max_cat not in ('—', None) else ''}投资类资产偏重" if max_cat == "investment" else f"{cat_labels.get(max_cat, max_cat)}偏重", "warn" if max_pct and max_pct > 0.6 else "neutral")

    # ---------- 3. 分类汇总 + 口径警示（左右两栏）----------
    col_summary, col_warn = st.columns([3, 2])
    with col_summary:
        section_title("分类汇总", right_html="先看清家庭结构，再看明细。")
        cat_totals = metrics.get("catTotals", {})
        assets = household[household["type"] == "asset"].copy()
        liabs = household[household["type"] == "liability"].copy()

        # 6 张子卡片（3 列 x 2 行）
        row1 = st.columns(3)
        row2 = st.columns(3)

        asset_cat_order = [
            ("cash", "现金及等价"),
            ("investment", "投资"),
            ("property", "房产"),
        ]
        for i, (cat_en, cat_cn) in enumerate(asset_cat_order):
            val = cat_totals.get(cat_en, 0)
            pct = val / metrics.get("A", 1) * 100 if metrics.get("A", 0) > 0 else 0
            desc_map = {"cash": "高流动性", "investment": f"占净值 {metrics.get('investRatio', 0):.0%}" if metrics.get('investRatio') else "", "property": "低流动性"}
            with row1[i]:
                sub_card(cat_cn, hkd_short(val), desc_map.get(cat_en, f"{pct:.0f}%"))

        liab_totals = {}
        for cat in liabs["category"].unique():
            liab_totals[cat] = liabs[liabs["category"] == cat]["hkd"].sum()

        debt_cat_order = [
            ("other", "其他资产"),
            ("mortgage", "房贷"),
            ("consumer", "消费贷/卡债"),
        ]
        for i, (cat_en, cat_cn) in enumerate(debt_cat_order):
            if cat_en in cat_totals:
                val = cat_totals[cat_en]
                desc = "补充缓冲"
            else:
                val = liab_totals.get(cat_en, 0)
                desc = "月供来源稳定" if cat_en == "mortgage" else "高成本负债"
            with row2[i]:
                sub_card(cat_cn, hkd_short(val), desc)

    with col_warn:
        section_title("口径警示", right_html='<span class="hf-pill hf-pill-yellow">会话内编辑</span>')
        st.markdown(f"""
        <div class="hf-card" style="padding:18px 20px;background:{TOKEN['yellow_bg']}">
            <div style="font-size:13px;color:{TOKEN['yellow']};font-weight:600;margin-bottom:10px">⚠️ 口径警示</div>
            <div style="font-size:13px;color:{TOKEN['text_primary']};line-height:1.6;margin-bottom:14px">
                发现会高估家庭抗风险能力的录入方式。
            </div>
            <div style="background:{TOKEN['bg_card_alt']};border-radius:8px;padding:12px 14px;margin-bottom:14px">
                <div style="font-size:12px;color:{TOKEN['yellow']};font-weight:600;margin-bottom:4px">⚠️ 投资类资产误标为 high</div>
                <div style="font-size:12px;color:{TOKEN['text_secondary']};line-height:1.6">
                    股票基金不应记为高流动性资产，否则会高估应急金覆盖能力。
                </div>
            </div>
            <div style="font-size:11.5px;color:{TOKEN['text_muted']};line-height:1.5">
                当前修改仅在会话内有效<br>
                若尚未写回原文件，请在重新加载前确认是否保留本次调整。
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------- 4. 资产负债明细 ----------
    section_title("资产负债明细", right_html="支持按类别筛选、直接编辑金额并重算。")

    # 统一表格
    assets_disp = assets[["name", "category", "amount", "currency", "hkd", "liquidity", "owner", "monthly_payment", "note"]].copy()
    assets_disp["type_hint"] = "asset"
    liabs_disp = liabs[["name", "category", "amount", "currency", "hkd", "owner", "monthly_payment", "note"]].copy()
    liabs_disp["liquidity"] = "—"
    liabs_disp["type_hint"] = "liability"
    # 统一列
    liabs_disp = liabs_disp[["name", "category", "amount", "currency", "hkd", "liquidity", "owner", "monthly_payment", "note", "type_hint"]]
    assets_disp = assets_disp[["name", "category", "amount", "currency", "hkd", "liquidity", "owner", "monthly_payment", "note", "type_hint"]]

    combined = pd.concat([assets_disp, liabs_disp], ignore_index=True)
    combined["category_cn"] = combined["category"].map(lambda x: cat_labels.get(x, x))
    combined["原币金额"] = combined.apply(lambda r: f"{r['currency']} {r['amount']:,.0f}", axis=1)
    combined["HKD 折算"] = combined["hkd"].apply(lambda x: hkd(x))
    combined["月供"] = combined["monthly_payment"].apply(lambda x: hkd(x) if pd.notna(x) and x != 0 else "—")
    combined["所有人"] = combined["owner"]
    combined["备注"] = combined["note"].fillna("")

    # 渲染 HTML 表格（深色样式）
    rows_html = []
    for _, r in combined.iterrows():
        is_liab = r["type_hint"] == "liability"
        # 流动性标记
        liq_val = r["liquidity"]
        if is_liab or liq_val == "—":
            liq_cell = '<span style="color:#5A6474">—</span>'
        else:
            lc = liq_colors.get(liq_val, "#8B949E")
            liq_cell = f'<span class="hf-pill hf-pill-{liq_val}" style="color:{lc};background:rgba(0,0,0,0.2)">{liq_pretty.get(liq_val, liq_val)}</span>'

        rows_html.append(f"""
        <tr>
            <td>{r['name']}</td>
            <td>{r['category_cn']}</td>
            <td>{r['原币金额']}</td>
            <td>{r['HKD 折算']}</td>
            <td>{liq_cell}</td>
            <td>{r['所有人']}</td>
            <td>{r['月供']}</td>
        </tr>""")

    table = f"""
    <table class="hf-table">
        <thead><tr>
            <th>科目</th><th>类别</th><th>原币金额</th><th>HKD 折算</th><th>流动性</th><th>所有人</th><th>月供</th>
        </tr></thead>
        <tbody>{"".join(rows_html)}</tbody>
    </table>
    """
    st.markdown(table, unsafe_allow_html=True)

    # 底部说明
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;margin-top:12px;font-size:11px;color:{TOKEN['text_muted']}">
        <span>金额先按汇率折算为 HKD，再进入汇总与风险计算。</span>
        <span>当前页面为结构核对视图</span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render_page()
