"""
P3 压力测试页
预置情景对比分析 - 击穿识别 + 建议
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
from src import (
    get_all_scenarios, compute_metrics, compute_all_limits,
    compare_scenarios, generate_conclusion,
)


def hkd_short(v):
    if v is None:
        return "—"
    if abs(v) >= 1_000_000:
        return f"HK${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"HK${v/1_000:.0f}K"
    return f"HK${v:,.0f}"


def hkd(v):
    if v is None:
        return "N/A"
    return f"HK${v:,.0f}"


def render_page():
    household = st.session_state.household
    cashflow = st.session_state.cashflow
    baseline_metrics = st.session_state.baseline_metrics
    baseline_limits = st.session_state.baseline_limits
    as_of = st.session_state.get("as_of", "")
    scenarios = get_all_scenarios()

    # ---------- 1. Header ----------
    header_html = f"""
    <div class="hf-header">
        <div>
            <h1 class="hf-header-title">压力测试</h1>
            <p class="hf-header-sub">用高置信情景识别收入中断、利率上升与资产贬值对家庭动态风险能力的冲击。</p>
        </div>
        <div class="hf-header-right">
            <div class="hf-header-chip">冲击方案 <br><b>联合压力</b></div>
            <div class="hf-header-chip">综合力 <br><span class="hf-pill hf-pill-yellow">🟡 黄灯</span></div>
            <div class="hf-header-chip">击穿项 <br><b style="color:{TOKEN['red']}">0 项</b></div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    _col_detail, _col_fill = st.columns([1, 9])
    with _col_detail:
        st.button("查看穿透详情 →", key="stress_btn_detail", use_container_width=True)

    # ---------- 2. 找到联合压力情景并计算 ----------
    # 默认使用第一个 income_mult=0 + invest_mult<1 的联合情景
    selected_sc = None
    for sc in scenarios:
        if sc.get("income_mult", 1) == 0 and sc.get("invest_mult", 1) < 1:
            selected_sc = sc
            break
    if selected_sc is None and scenarios:
        selected_sc = scenarios[0]

    shock = {k: selected_sc.get(k, 1.0) for k in
             ["income_mult", "essential_exp_mult", "invest_mult", "property_mult",
              "debt_service_mult", "liability_mult"]}
    stress_metrics = compute_metrics(household, cashflow, shock)
    stress_limits = compute_all_limits(stress_metrics)
    comparison = compare_scenarios(baseline_metrics, stress_metrics, baseline_limits, stress_limits)

    breaches = comparison.get("breaches", [])
    stress_light = stress_limits.get("overall", "green")
    base_light = baseline_limits.get("overall", "green")

    # ---------- 3. 击穿数大标题 ----------
    breach_count = len(breaches)
    big_num_color = TOKEN["yellow"] if breach_count == 0 else TOKEN["red"]
    big_num = "0" if breach_count == 0 else str(breach_count)

    big_html = f"""
    <div class="hf-overview-card" style="padding:24px 28px">
        <div style="display:flex;gap:28px;align-items:center">
            <div>
                <div style="font-size:64px;font-weight:800;color:{big_num_color};letter-spacing:-2px;line-height:1">
                    {big_num}
                </div>
            </div>
            <div>
                <div style="font-size:14px;color:{TOKEN['text_secondary']};margin-bottom:4px">击穿限额</div>
                <div style="font-size:16px;color:{TOKEN['text_primary']};font-weight:600;margin-bottom:8px">
                    {selected_sc['name']}
                </div>
                <div style="font-size:12.5px;color:{TOKEN['text_secondary']};line-height:1.6;max-width:480px">
                    {selected_sc.get('description', '')}
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(big_html, unsafe_allow_html=True)

    # ---------- 4. 冲击系数快捷按钮 ----------
    section_title("预警情景选择器", right_html="选择冲击系数，实时显示综合力变化，以及对应的应对建议。")

    shock_btns = [
        ("收入中断", "-70%", shock.get("income_mult"), "income_mult"),
        ("投资下跌", "-20%", shock.get("invest_mult"), "invest_mult"),
        ("供款上升", "+200bp", shock.get("debt_service_mult"), "debt_service_mult"),
        ("房产下跌", "-10%", shock.get("property_mult"), "property_mult"),
    ]
    btn_html = '<div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap">'
    for label, val, cur, key in shock_btns:
        cur_display = f"×{cur:.2f}" if cur else "×1.00"
        btn_html += f'''
        <div class="hf-sub-card" style="flex:1;min-width:180px;cursor:pointer">
            <div style="font-size:11px;color:{TOKEN['text_secondary']};margin-bottom:2px">{label}</div>
            <div style="font-size:18px;font-weight:700;color:{TOKEN['text_primary']}">{val}</div>
            <div style="font-size:10.5px;color:{TOKEN['text_muted']};margin-top:2px">当前 {cur_display}</div>
        </div>'''
    btn_html += '</div>'
    st.markdown(btn_html, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-size:12px;color:{TOKEN['text_secondary']};padding:8px 4px">
        <span style="color:{TOKEN['yellow']};font-weight:600">联合压力</span>
        会把家庭迅速推入红灯，优先级必须切到<span style="color:{TOKEN['yellow']}">补流动性与降债务服务</span>。
    </div>""", unsafe_allow_html=True)

    # ---------- 5. 基准 vs 压力（黄灯·可管理 vs 红灯·需立即处置）----------
    section_title("联合压力对比", right_html=f"当前情景：{selected_sc['name']}")

    col_base, col_stress = st.columns(2)

    base_values = {
        "净值": baseline_metrics.get("E", 0),
        "流动性月数": baseline_metrics.get("LIM"),
        "DSTI": baseline_metrics.get("DSTI"),
    }
    stress_values = {
        "净值": stress_metrics.get("E", 0),
        "流动性月数": stress_metrics.get("LIM"),
        "DSTI": stress_metrics.get("DSTI"),
    }

    # 基准列
    base_light_label, base_light_color, _ = STATUS_MAP.get(base_light, STATUS_MAP["green"])
    with col_base:
        st.markdown(f"""
        <div class="hf-card" style="border-top:3px solid {base_light_color};padding:18px 22px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
                <span style="font-size:14px;font-weight:600;color:{TOKEN['text_primary']}">基准 · 当前</span>
                <span class="hf-pill hf-pill-{base_light}" style="background:{TOKEN[base_light+'_bg']}">{base_light_label}</span>
            </div>
        """, unsafe_allow_html=True)
        metric_card("净值 E", hkd_short(base_values["净值"]))
        metric_card("流动性月数", f"{base_values['流动性月数']:.1f} 月" if base_values["流动性月数"] else "N/A")
        dsti_b = base_values["DSTI"]
        metric_card("DSTI", f"{dsti_b:.0%}" if dsti_b and dsti_b != float('inf') else "N/A")
        st.markdown("</div>", unsafe_allow_html=True)

    # 压力列
    stress_light_label, stress_light_color, _ = STATUS_MAP.get(stress_light, STATUS_MAP["green"])
    with col_stress:
        st.markdown(f"""
        <div class="hf-card" style="border-top:3px solid {stress_light_color};padding:18px 22px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">
                <span style="font-size:14px;font-weight:600;color:{TOKEN['text_primary']}">{selected_sc['name']}</span>
                <span class="hf-pill hf-pill-{stress_light}" style="background:{TOKEN[stress_light+'_bg']}">{stress_light_label} · {'可管理' if stress_light == 'yellow' else '需立即处置'}</span>
            </div>
        """, unsafe_allow_html=True)
        metric_card("净值 E", hkd_short(stress_values["净值"]))
        metric_card("流动性月数", f"{stress_values['流动性月数']:.1f} 月" if stress_values["流动性月数"] else "N/A")
        dsti_s = stress_values["DSTI"]
        metric_card("DSTI", f"{dsti_s:.0%}" if dsti_s and dsti_s != float('inf') else "N/A")
        st.markdown("</div>", unsafe_allow_html=True)

    # 变化说明
    e_diff = stress_values["净值"] - base_values["净值"]
    lim_diff = (stress_values["流动性月数"] or 0) - (base_values["流动性月数"] or 0)
    st.markdown(f"""
    <div style="margin-top:14px;padding:12px 16px;background:{TOKEN['bg_card']};border-radius:8px;border-left:3px solid {TOKEN['yellow']}">
        <div style="font-size:12.5px;color:{TOKEN['text_primary']}">
            <b>流动性月数降至 {stress_values['流动性月数']:.1f} 月。</b>{"" if breach_count > 0 else "当前仍在 3 月以上，但已接近黄线下限。"}
        </div>
        <div style="font-size:11.5px;color:{TOKEN['text_muted']};margin-top:4px">
            DSTI 升至 {dsti_s:.0%}（+{(dsti_s or 0) - (dsti_b or 0):+.0%}），债务服务明显增加。
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ---------- 6. 击穿/局限清单 ----------
    section_title("击穿/局限清单", right_html=f'<span class="hf-pill hf-pill-red">{breach_count} 项</span>' if breach_count else "")

    if breaches:
        for i, b in enumerate(breaches, 1):
            st.markdown(f"""
            <div class="hf-breach-item">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                    <div><span class="hf-breach-num">{i}</span><b style="color:{TOKEN['text_primary']}">{b['name']}</b></div>
                    <span class="hf-pill hf-pill-red">红灯</span>
                </div>
                <div style="font-size:12px;color:{TOKEN['text_secondary']};line-height:1.6">
                    {b['reason']}<br>
                    基准：{b['baseline_status']} → 压力：{b['stress_status']}
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        # 没有击穿则显示"局限项"
        lim_stress = stress_metrics.get("LIM")
        gaps = []
        if lim_stress and lim_stress < 6:
            gaps.append(f"流动性月数 {lim_stress:.1f} < 6 月目标，处于黄灯区")
        dsti_s = stress_metrics.get("DSTI")
        if dsti_s and dsti_s > 0.4:
            gaps.append(f"DSTI {dsti_s:.0%} 高于 40% 警戒")

        if gaps:
            for i, g in enumerate(gaps, 1):
                st.markdown(f"""
                <div class="hf-breach-item" style="border-left:3px solid {TOKEN['yellow']}">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                        <div><span class="hf-breach-num" style="background:{TOKEN['yellow_bg']};color:{TOKEN['yellow']}">{i}</span><b style="color:{TOKEN['text_primary']}">局限项 #{i}</b></div>
                        <span class="hf-pill hf-pill-yellow">黄灯</span>
                    </div>
                    <div style="font-size:12px;color:{TOKEN['text_secondary']};line-height:1.6">{g}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="hf-card" style="text-align:center;padding:24px;color:{TOKEN["text_muted"]}">🟢 该情景下无限额击穿</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ---------- 7. 结论与建议 ----------
    col_conclusion, col_suggestion = st.columns([2, 3])
    with col_conclusion:
        section_title("结论", right_html=f"综合力 {STATUS_MAP.get(stress_light, STATUS_MAP['green'])[0]}")
        conclusion = generate_conclusion(selected_sc['name'], comparison, stress_metrics.get("unemployment"))
        st.markdown(f"""
        <div class="hf-card" style="padding:16px 20px">
            <div style="font-size:13px;color:{TOKEN['text_primary']};line-height:1.7">
                {conclusion}
            </div>
        </div>""", unsafe_allow_html=True)

    with col_suggestion:
        section_title("建议", right_html="针对本家庭最直接可落地的处置。")
        suggestions = []
        if (stress_metrics.get("LIM") or 99) < 6:
            suggestions.append(("补足应急金", "优先将应急金提升至 6 个月必要支出以上。可用现金 + 货币基金作为应急主体。"))
        if (stress_metrics.get("DSTI") or 0) > 0.4:
            suggestions.append(("降低债务服务", "考虑提前偿还高成本消费贷，或延长剩余房贷期限降低月供。"))
        if baseline_metrics.get("investRatio", 0) and baseline_metrics.get("investRatio", 0) > 0.6:
            suggestions.append(("分散资产配置", "投资占净值过高（≈{:.0%}），建议增配稳健现金及固收类缓冲。".format(baseline_metrics.get("investRatio", 0))))
        if baseline_metrics.get("incomeSources", 0) <= 1:
            suggestions.append(("拓展收入来源", "单一收入来源 + 偏低流动性使家庭在失业情景下极脆弱，优先拓展副业。"))

        # 如果没有建议，给通用建议
        if not suggestions:
            suggestions = [("维持当前结构", "当前家庭在联合压力下仍维持绿灯，继续监控即可。")]

        for i, (title, body) in enumerate(suggestions, 1):
            st.markdown(f"""
            <div class="hf-sub-card" style="margin-bottom:8px">
                <div style="display:flex;gap:10px;align-items:flex-start">
                    <div style="flex-shrink:0;width:20px;height:20px;border-radius:50%;background:{TOKEN['blue']};
                                color:white;font-size:11px;font-weight:700;display:flex;align-items:center;
                                justify-content:center">{i}</div>
                    <div>
                        <div style="font-size:13px;font-weight:600;color:{TOKEN['text_primary']};margin-bottom:2px">{title}</div>
                        <div style="font-size:12px;color:{TOKEN['text_secondary']};line-height:1.6">{body}</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    render_page()
