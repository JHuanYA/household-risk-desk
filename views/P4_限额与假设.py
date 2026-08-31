"""
P4 限额与假设页
集中说明限额定义、触发条件、适用范围与关键假设
"""

import streamlit as st
import pandas as pd
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.theme import (
    metric_card, sub_card, section_title, pill,
    TOKEN, STATUS_MAP, _set_page,
)
from src import load_limits_config


def render_page():
    limits_result = st.session_state.baseline_limits
    as_of = st.session_state.get("as_of", "")
    overall = limits_result.get("overall", "green")
    config = load_limits_config()

    # ---------- 1. Header ----------
    header_html = f"""
    <div class="hf-header">
        <div>
            <h1 class="hf-header-title">限额与假设</h1>
            <p class="hf-header-sub">非正式风险报告一员，把限额、定义与口径说清楚。所有阈值均结合适用范围与数据完整性一并解读。</p>
        </div>
        <div class="hf-header-right">
            <div class="hf-header-chip">汇率日期 <br><b>{as_of}</b></div>
            <div class="hf-header-chip">当前配置 <br><b>家庭默认 · 联合压力</b></div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    _col_export, _col_fill = st.columns([1, 9])
    with _col_export:
        st.button("导出简报与说明 →", key="limits_btn_export", use_container_width=True)

    # ---------- 2. 三个顶部概念卡片 ----------
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="hf-card" style="padding:20px 22px">
            <div class="hf-card-title" style="color:{TOKEN['blue']}">季度复核</div>
            <div style="font-size:15px;color:{TOKEN['text_primary']};font-weight:600;margin-bottom:6px">
                观察指标、输入稳定性与条件变化
            </div>
            <div style="font-size:12px;color:{TOKEN['text_secondary']};line-height:1.6">
                建议每季度复核一次家庭风险限额参数，或在收入/负债/资产出现显著变化时即时复核。
            </div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="hf-card" style="padding:20px 22px">
            <div class="hf-card-title" style="color:{TOKEN['text_secondary']}">绿 / 黄 / 红</div>
            <div style="display:flex;gap:10px;margin:10px 0">
                <span class="hf-pill hf-pill-green">绿灯</span>
                <span class="hf-pill hf-pill-yellow">黄灯</span>
                <span class="hf-pill hf-pill-red">红灯</span>
            </div>
            <div style="font-size:12px;color:{TOKEN['text_secondary']};line-height:1.6">
                分别代表正常警戒、接近限额、触发红线。综合灯取所有指标中的最差者。
            </div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="hf-card" style="padding:20px 22px;border-color:{TOKEN['yellow']}">
            <div class="hf-card-title" style="color:{TOKEN['yellow']}">缺项不判绿灯</div>
            <div style="font-size:15px;color:{TOKEN['text_primary']};font-weight:600;margin-bottom:6px">
                必要支出、债务供款、主要资产任一缺失，只能维持黄灯。
            </div>
            <div style="font-size:12px;color:{TOKEN['text_secondary']};line-height:1.6">
                数据完整性优先于数值达标，避免在口径缺失时给出绿灯造成误导。
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ---------- 3. 限额表 ----------
    section_title("限额表", right_html="以下为总览页和压力测试页用到的全部限额指标。")

    limits = limits_result.get("limits", [])
    table_rows = []
    for l in limits:
        sid = l["id"]
        name = l["name"]
        display = l.get("display", "—")
        status = l.get("status", "green")
        yellow = l.get("yellow", "—")
        red = l.get("red", "—")
        reason = l.get("reason", "")

        # 适用范围说明
        scope_map = {
            "LIM": "流动性视角（high 级应急金）",
            "LEV": "资产负债表视角",
            "E": "净值视角",
            "DSTI": "现金流视角（债务服务/收入）",
            "INVEST": "集中度视角（分母用净值 E）",
            "CONC": "最大类别集中度",
            "INCOME": "单一收入视角 + LIM 联动",
        }
        scope = scope_map.get(sid, "")

        # 口径提示
        hint_map = {
            "LIM": "必要支出为口径（essential=1）",
            "LEV": "负债 L / 资产 A",
            "E": "资产 - 负债",
            "DSTI": "债务供款 DS / 月收入 INC",
            "INVEST": "投资类资产 / 净值 E",
            "CONC": "最大类别资产 / 净值 E",
            "INCOME": "来源 ≤ 1 且 LIM<6 才判红灯",
        }
        hint = hint_map.get(sid, "")

        pill_html = f'<span class="hf-pill hf-pill-{status}">{STATUS_MAP.get(status, STATUS_MAP["green"])[0]}</span>'
        status_map = {"green": TOKEN["green"], "yellow": TOKEN["yellow"], "red": TOKEN["red"]}
        table_rows.append(f"""
        <tr>
            <td><b>{name}</b><br><span style="font-size:11px;color:{TOKEN['text_muted']}">{sid}</span></td>
            <td><b style="color:{status_map.get(status,'')}">{display}</b><br>{pill_html}</td>
            <td>{yellow}</td>
            <td style="color:{TOKEN['red']}">{red}</td>
            <td>{scope}</td>
            <td style="color:{TOKEN['text_secondary']}">{hint}</td>
        </tr>""")

    table_html = f"""
    <table class="hf-table">
        <thead><tr>
            <th>指标</th><th>当前值 / 状态</th><th>黄灯预警</th><th>红线</th><th>适用范围</th><th>口径提示</th>
        </tr></thead>
        <tbody>{"".join(table_rows)}</tbody>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top:10px;font-size:11.5px;color:{TOKEN['text_muted']}">
        判定顺序：先校验输入完整性，再套用阈值。若口径缺失，不得因为数值刚好达标而给出绿灯。
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ---------- 4. 风险事件定义 + 关键假设摘要 + 适用不适用 ----------
    col_left, col_right = st.columns([3, 2])

    with col_left:
        section_title("关键假设摘要", right_html="默认写在场景字典中，可随时人工更新，但建议建立在硬限额之上。")

        assumptions = [
            ("必要支出口径", "cashflow 中 essential=1 的流出作为分母；一次性大额支出、娱乐等不应计为必要支出。", TOKEN["blue"]),
            ("估值与汇率日期", "资产按当日汇率折算为 HKD。若估值陈旧，建议在重新加载前修正。", TOKEN["green"]),
            ("收入稳定性处理", "每月收入固定，副业与工资在口径上等价。失业情景只把 income_mult 置为 0。", TOKEN["yellow"]),
            ("高流动性资产定义", "仅包含 cash 类别下 liquidity=high 的条目，房产、股票与强积金不计入 LIM 分子。", TOKEN["blue"]),
        ]
        for title, body, color in assumptions:
            st.markdown(f"""
            <div class="hf-sub-card" style="margin-bottom:8px;border-left:3px solid {color}">
                <div style="font-size:13px;font-weight:600;color:{TOKEN['text_primary']};margin-bottom:4px">{title}</div>
                <div style="font-size:12px;color:{TOKEN['text_secondary']};line-height:1.6">{body}</div>
            </div>""", unsafe_allow_html=True)

    with col_right:
        section_title("风险事件定义", right_html="")
        events = [
            ("流动性断裂", "LIM < 目标月数", "high"),
            ("偿付危机", "净值 E < 0", "red"),
            ("债务服务压力", "DSTI > 0.5", "red"),
            ("过度集中", "单一类别 / 净值 > 0.7", "yellow"),
            ("收入单一脆弱", "收入来源 ≤ 1 且 LIM < 6", "yellow"),
        ]
        for name, cond, tone in events:
            st.markdown(f"""
            <div class="hf-sub-card" style="margin-bottom:6px;padding:10px 14px">
                <div style="display:flex;justify-content:space-between;align-items:center">
                    <div style="font-size:13px;color:{TOKEN['text_primary']};font-weight:500">{name}</div>
                    <span class="hf-pill hf-pill-{tone}" style="font-size:10px">{cond}</span>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ---------- 5. 适用与不适用 ----------
    section_title("适用与不适用说明", right_html="")

    col_apply, col_not_apply = st.columns(2)
    with col_apply:
        st.markdown(f"""
        <div class="hf-card" style="padding:18px 20px;border-top:3px solid {TOKEN['green']}">
            <div style="font-size:13px;font-weight:600;color:{TOKEN['green']};margin-bottom:8px">✅ 适用</div>
            <div style="font-size:12.5px;color:{TOKEN['text_primary']};line-height:1.7">
                适用于已有完整资产、现金流、房产与负债记录的家庭。<br>
                家庭风险检视、作品演示、资产配置与压力情景回顾。
            </div>
        </div>""", unsafe_allow_html=True)
    with col_not_apply:
        st.markdown(f"""
        <div class="hf-card" style="padding:18px 20px;border-top:3px solid {TOKEN['red']}">
            <div style="font-size:13px;font-weight:600;color:{TOKEN['red']};margin-bottom:8px">🚫 不适用</div>
            <div style="font-size:12.5px;color:{TOKEN['text_primary']};line-height:1.7">
                不用于替代专业风险评估、正式借贷文件、投资建议。<br>
                用于数据极度匮乏或完全缺失的家庭。
            </div>
        </div>""", unsafe_allow_html=True)

    # 底部 disclaimer
    st.markdown(f"""
    <div style="margin-top:20px;padding-top:14px;border-top:1px solid {TOKEN['border']};
                font-size:11px;color:{TOKEN['text_muted']};line-height:1.6;text-align:center">
        风险基于经验口径，不替代人工判断；所有结论与建议应保留适用范围与数据假设。
        <br>当前页面为演示配置
    </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    render_page()
