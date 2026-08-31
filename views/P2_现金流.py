"""
P2 现金流页
从现金流视角判断家庭能否支撑必要支出和债务供款
"""

import streamlit as st
import pandas as pd
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.theme import (
    metric_card, section_title, pill,
    TOKEN, STATUS_MAP, _set_page,
)


def hkd_short(v):
    if v is None:
        return "—"
    if abs(v) >= 1_000:
        return f"HK${v/1_000:.0f}K"
    return f"HK${v:,.0f}"


def hkd(v):
    if v is None:
        return "—"
    return f"HK${v:,.0f}"


def render_page():
    cashflow = st.session_state.cashflow
    metrics = st.session_state.baseline_metrics
    as_of = st.session_state.get("as_of", "")

    # ---------- 1. Header ----------
    light = st.session_state.baseline_limits.get("overall", "green")
    header_html = f"""
    <div class="hf-header">
        <div>
            <h1 class="hf-header-title">现金流</h1>
            <p class="hf-header-sub">从现金流视角判断家庭能否支撑必要支出和债务供款。</p>
        </div>
        <div class="hf-header-right">
            <div class="hf-header-chip"><span class="hf-pill hf-pill-green">必要支出状态</span></div>
            <div class="hf-header-chip"><span class="hf-pill hf-pill-blue">已录入</span></div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    _col_stress, _col_fill = st.columns([1, 9])
    with _col_stress:
        st.button("带入压力测试 →", key="cashflow_btn_to_stress",
                  on_click=_set_page, args=("stress",), use_container_width=True)

    # ---------- 2. 四张顶部卡片 ----------
    inc = metrics.get("INC", 0)
    exp_ess = metrics.get("EXP_ess", 0)
    ds = metrics.get("DS", 0)
    cf = metrics.get("CF", 0)
    dsti = metrics.get("DSTI")
    dsti_pct = f"{dsti:.0%}" if dsti else "—"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("月收入", hkd_short(inc), "1 条主工资 + 1 条副业", "neutral")
    with col2:
        metric_card("必要支出", hkd_short(exp_ess), "流动性分母核心口径", "neutral")
    with col3:
        metric_card("债务供款", hkd_short(ds), f"DSTI 达 {dsti_pct}",
                    "warn" if dsti and dsti > 0.4 else "neutral")
    with col4:
        metric_card("月结余", hkd_short(cf),
                    "缓冲偏薄" if cf < 20_000 else "缓冲尚可",
                    "warn" if cf < 10_000 else "good")

    st.markdown("---")

    # ---------- 3. 收入来源 + 支出结构（左右）----------
    col_income, col_expense = st.columns([3, 2])

    with col_income:
        section_title("收入来源结构", right_html="主要收入集中意味着失业情景下的脆弱性更高。")

        incomes = cashflow[cashflow["direction"] == "in"].sort_values("source_rank", na_position="last")
        income_total = incomes["hkd"].sum()

        for _, row in incomes.iterrows():
            rank = int(row.get("source_rank", 99)) if pd.notna(row.get("source_rank")) else "—"
            pct = row["hkd"] / income_total * 100 if income_total > 0 else 0
            st.markdown(f"""
            <div class="hf-sub-card" style="margin-bottom:8px;padding:12px 16px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                    <div style="font-size:13.5px;font-weight:600;color:{TOKEN['text_primary']}">{row['name']}</div>
                    <div style="font-size:14px;font-weight:600;color:{TOKEN['text_primary']}">{hkd_short(row['hkd'])}</div>
                </div>
                <div style="font-size:11.5px;color:{TOKEN['text_secondary']};margin-bottom:6px">
                    来源 rank {rank}，占总收入 {pct:.0f}%
                </div>
                <div style="background:{TOKEN['bg_elev']};border-radius:4px;height:4px;overflow:hidden">
                    <div style="width:{pct:.1f}%;background:{TOKEN['blue']};height:100%"></div>
                </div>
            </div>""", unsafe_allow_html=True)

        # 底部提示
        income_count = metrics.get("incomeSources", 0)
        primary_pct = incomes.iloc[0]["hkd"] / income_total * 100 if len(incomes) > 0 and income_total > 0 else 0
        st.markdown(f"""
        <div class="hf-alert hf-alert-yellow" style="border-left-color:{TOKEN['yellow']};margin-top:10px">
            <div class="hf-alert-header">
                <span class="hf-pill hf-pill-yellow">⚠️</span>
                <span class="hf-alert-title">收入来源仅 {income_count} 条，其中主工资占比过高</span>
            </div>
            <div class="hf-alert-body">若主工资中断，应急金不足的风险会被立即放大。</div>
        </div>""", unsafe_allow_html=True)

    with col_expense:
        section_title("支出结构", right_html="必要支出和债务供款共同决定家庭现金流下限。")

        exp_all = metrics.get("EXP_all", 1)
        exp_ess_only = exp_ess - ds
        exp_non_ess = exp_all - exp_ess

        # 水平条形图
        bar_items = [
            ("必要支出", exp_ess_only, TOKEN["blue"]),
            ("债务供款", ds, TOKEN["yellow"]),
            ("非必要支出", exp_non_ess, TOKEN["text_muted"]),
        ]
        for label, val, color in bar_items:
            pct = val / exp_all * 100 if exp_all > 0 else 0
            st.markdown(f"""
            <div style="margin-bottom:14px">
                <div style="display:flex;justify-content:space-between;font-size:12.5px;margin-bottom:4px">
                    <span style="color:{TOKEN['text_primary']}">{label}</span>
                    <span style="color:{TOKEN['text_secondary']}">{pct:.0f}%</span>
                </div>
                <div style="background:{TOKEN['bg_elev']};border-radius:4px;height:14px;overflow:hidden">
                    <div style="width:{pct:.1f}%;background:{color};height:100%;border-radius:4px"></div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ---------- 4. 强提醒横幅 ----------
    section_title("强提醒", right_html="现金流录入是流动性口径的前提，缺项也不能静默置零。")
    st.markdown(f"""
    <div class="hf-card" style="background:{TOKEN['yellow_bg']};border-color:{TOKEN['yellow']};padding:18px 24px">
        <div style="font-size:16px;font-weight:600;color:{TOKEN['text_primary']};margin-bottom:6px">
            必要支出若为 0，则 LIM 不可用且不能给绿灯。
        </div>
        <div style="font-size:12px;color:{TOKEN['text_secondary']}">
            当前 Demo 数据已录入必要支出，口径完整。
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ---------- 5. 现金流明细 ----------
    section_title("现金流明细", right_html="收入、必要、非必要支出和债务供款统一核对。")

    # 统一表格
    rows_html = []
    for _, r in cashflow.iterrows():
        direction = "in" if r["direction"] == "in" else "out"
        dir_label = "收入" if direction == "in" else "支出"
        dir_color = TOKEN["green"] if direction == "in" else TOKEN["red"]
        ess_mark = "是" if r.get("essential", 0) == 1 else "—"
        ds_mark = "是" if r.get("debt_service", 0) == 1 else "—"
        rank = int(r.get("source_rank", 0)) if pd.notna(r.get("source_rank")) else "—"

        # 方向用颜色标记
        dir_cell = f'<span style="color:{dir_color};font-weight:600">{dir_label}</span>'

        rows_html.append(f"""
        <tr>
            <td>{r['name']}</td>
            <td>{dir_cell}</td>
            <td>{r['monthly_amount']:,.0f}</td>
            <td>{r['currency']}</td>
            <td>{hkd(r['hkd'])}</td>
            <td>{ess_mark}</td>
            <td>{ds_mark}</td>
            <td>{rank}</td>
        </tr>""")

    table = f"""
    <table class="hf-table">
        <thead><tr>
            <th>项目</th><th>方向</th><th>月金额</th><th>币种</th><th>HKD 折算</th><th>必要</th><th>债务服务</th><th>来源 rank</th>
        </tr></thead>
        <tbody>{"".join(rows_html)}</tbody>
    </table>
    """
    st.markdown(table, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;margin-top:12px;font-size:11px;color:{TOKEN['text_muted']}">
        <span>现金流指标默认以 cashflow 表中 debt_service=1 的流出为主口径。</span>
        <span>当前页面用于现金流压力诊断</span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render_page()
