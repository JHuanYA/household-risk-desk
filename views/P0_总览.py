"""
P0 总览页 - 家庭风险态势总览
30秒识别家庭是否处在流动性、杠杆与债务服务压力下
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.theme import (
    header, metric_card, alert_card, overview_big_light,
    sub_card, section_title, pill, action_btn, dark_plotly_layout,
    TOKEN, STATUS_MAP, _set_page,
)
from src import (
    compute_metrics, compute_all_limits,
    get_all_scenarios, compare_scenarios, load_all_data, get_data_dir,
)


# ===== 工具函数 =====
def hkd(v):
    if v is None:
        return "N/A"
    return f"HK${v:,.0f}"


def hkd_short(v):
    """紧凑 HK$ 格式"""
    if v is None:
        return "N/A"
    if abs(v) >= 1_000_000:
        return f"HK${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"HK${v/1_000:.0f}K"
    return f"HK${v:,.0f}"


# ===== 主渲染 =====
def render_overview_page():
    metrics = st.session_state.baseline_metrics
    limits = st.session_state.baseline_limits
    overall = limits.get("overall", "green")
    alerts = limits.get("alerts", [])
    as_of = st.session_state.get("as_of", "")

    # ---------- 1. 顶部 Header ----------
    light_label, light_color, _ = STATUS_MAP.get(overall, STATUS_MAP["green"])
    header_html = f"""
    <div class="hf-header">
        <div>
            <h1 class="hf-header-title">家庭风险态势总览</h1>
            <p class="hf-header-sub">30秒识别当前家庭是否处在流动性、杠杆与债务服务压力下。</p>
        </div>
        <div class="hf-header-right">
            <div class="hf-header-chip">汇率日期 <br><b>{as_of}</b></div>
            <div class="hf-header-chip" style="border-color:{light_color};background:rgba(0,0,0,0)">
                综合灯 <br><span class="hf-pill hf-pill-{overall}" style="font-size:11px">{light_label} · 预警</span>
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # Header 按钮（SPA 路由）
    _col_reload, _col_stress, _col_fill = st.columns([1, 1, 8])
    with _col_reload:
        st.button("重新加载", key="overview_btn_reload", use_container_width=True)
    with _col_stress:
        st.button("进入压力测试 →", key="overview_btn_to_stress",
                  on_click=_set_page, args=("stress",), use_container_width=True)

    # ---------- 2. 综合风险总卡 ----------
    desc_parts = []
    if overall == "yellow":
        desc_parts.append("流动性缓冲不足，投资占净值偏高；联合情景下现金缺口进一步扩大。")
    elif overall == "red":
        desc_parts.append("关键指标已击穿红线，建议立即处置。")
    else:
        desc_parts.append("核心指标均在安全区内，维持当前结构即可。")

    # 状态胶囊
    trend = "当前模式" if overall == "green" else "趋势判断"
    trend_val = "Demo 家庭"
    trend_val2 = "中度风险暴露" if overall != "green" else "绿灯"
    priority = "建议优先级" if overall != "green" else ""
    priority_val = "先补流动性" if overall != "green" else ""

    actions_html = f"""
    <div style="display:flex;gap:8px;flex-wrap:wrap">
        <span class="hf-pill hf-pill-blue">{trend_val}</span>
        <span class="hf-pill hf-pill-{'yellow' if overall!='green' else 'green'}">{trend_val2}</span>
        {f'<span class="hf-pill hf-pill-yellow">{priority_val}</span>' if priority else ''}
    </div>
    """
    overview_big_light(overall, " ".join(desc_parts), actions_html)

    # overview_big_light 下方的跳转按钮
    _col_sres, _col_limits, _col_fill2 = st.columns([1, 1, 8])
    with _col_sres:
        st.button("查看压力结果 →", key="overview_btn_stress_result",
                  on_click=_set_page, args=("stress",), use_container_width=True)
    with _col_limits:
        st.button("查看限额明细 →", key="overview_btn_limits_detail",
                  on_click=_set_page, args=("limits",), use_container_width=True)

    # ---------- 3. 指标卡（4 列，右侧告警 + 饼图 2 列合并布局）----------
    # 左侧 4 张紧凑卡 + 右侧 DSTI + 资产结构
    col_metric_e, col_metric_lev, col_metric_lim, col_metric_gap = st.columns(4)

    with col_metric_e:
        e = metrics.get("E", 0)
        metric_card("净值 E", hkd_short(e), "压力后仍为正，但缓冲中度", "neutral")
    with col_metric_lev:
        lev = metrics.get("LEV", 0)
        lev_pct = f"{lev:.1%}" if lev else "N/A"
        lev_warn = lev and lev > 0.4
        metric_card("杠杆 L/A", lev_pct,
                    "高于目标 40%" if lev_warn else "在目标内",
                    "warn" if lev_warn else "good")
    with col_metric_lim:
        lim = metrics.get("LIM")
        lim_display = f"{lim:.1f} 月" if lim else "N/A"
        lim_warn = lim is not None and lim < 6
        metric_card("流动性月数 LIM", lim_display,
                    "低于目标 6 月" if lim_warn else "达标",
                    "warn" if lim_warn else ("bad" if lim and lim < 3 else "good"))
    with col_metric_gap:
        gap = metrics.get("GAP")
        metric_card("应急金缺口 GAP", hkd_short(gap),
                    "补足后可回到限额内" if gap and gap > 0 else "无缺口",
                    "warn" if gap and gap > 0 else "good")

    # 下一行：DSTI + 空 + 资产结构饼图
    col_left2, col_right2 = st.columns([3, 2])
    with col_left2:
        dsti = metrics.get("DSTI")
        dsti_display = f"{dsti:.1%}" if dsti else "N/A"
        dsti_warn = dsti and dsti > 0.4
        metric_card("DSTI", dsti_display,
                    "债务服务偏高" if dsti_warn else "偿债压力合理",
                    "warn" if dsti_warn else "good")

    # ---------- 4. 非绿灯告警 + 资产结构饼图（左右两栏）----------
    col_alerts, col_pie = st.columns([3, 2])

    with col_alerts:
        section_title("非绿灯告警",
                      right_html=f'<span class="hf-pill hf-pill-yellow">{len(alerts)} 项重点预警</span>' if alerts else "")
        if alerts:
            for a in alerts:
                # 构建告警 body
                body = a.get("reason", "")
                current = a.get("display", "")
                # 尝试找到 "当前值 vs 目标" 的结构
                # alert_card 会把 {} 里的内容高亮
                name = a.get("name", "")
                # 格式化描述
                body_formatted = body
                status = a.get("status", "yellow")
                alert_card(status, name, body_formatted)
        else:
            st.markdown(f'<div class="hf-card" style="text-align:center;padding:28px;color:{TOKEN["text_muted"]}">✅ 所有风险指标均在限额内</div>', unsafe_allow_html=True)

    with col_pie:
        section_title("资产结构", right_html="以净值结构观察风险集中度，而不是只看总资产。")
        cat_labels = {"cash": "现金及等价", "investment": "投资", "property": "房产", "other": "其他资产"}
        cat_totals = metrics.get("catTotals", {})
        e_total = metrics.get("E", 1) or 1

        if cat_totals:
            # 饼图数据 —— 以净值为分母（原型图标注的是净值结构）
            pie_labels = []
            pie_values = []
            for cat, amt in cat_totals.items():
                pie_labels.append(cat_labels.get(cat, cat))
                pie_values.append(amt)

            # 环形图
            colors_map = {
                "现金及等价": "#58A6FF",
                "投资": "#3FB950",
                "房产": "#F0B429",
                "其他资产": "#8B949E",
            }
            fig = go.Figure(data=[go.Pie(
                labels=pie_labels,
                values=pie_values,
                hole=0.62,
                marker_colors=[colors_map.get(l, "#58A6FF") for l in pie_labels],
                textfont=dict(color=TOKEN["text_primary"], size=11),
                textinfo="percent",
                hovertemplate="<b>%{label}</b><br>HK$%{value:,.0f}<br>占比 %{percent}<extra></extra>",
            )])
            # 中间加净值文字
            e_display = f"HK${metrics.get('E', 0)/1_000_000:.2f}M"
            fig.add_annotation(
                text=f"净值<br><b style='font-size:20px;color:{TOKEN['text_primary']}'>{e_display}</b>",
                x=0.5, y=0.5, showarrow=False, align="center",
                font=dict(size=12, color=TOKEN["text_secondary"]),
            )
            fig = dark_plotly_layout(fig, height=280)
            fig.update_layout(showlegend=True,
                              legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5,
                                          font=dict(size=10.5, color=TOKEN["text_secondary"])))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无资产数据")

    st.markdown("---")

    # ---------- 5. 压力情景快捷预览 ----------
    section_title("压力情景快捷预览", right_html="默认展示主情景：失业 + 投资下跌 20%")

    scenarios = get_all_scenarios()
    # 找失业 + 投资下跌的情景（常见是"联合压力"或默认情景）
    default_sc = None
    for sc in scenarios:
        if sc.get("default") or (sc.get("income_mult") == 0 and sc.get("invest_mult", 1) < 1):
            default_sc = sc
            break
    if default_sc is None and scenarios:
        default_sc = scenarios[0]

    if default_sc:
        shock = {k: default_sc.get(k, 1.0) for k in
                 ["income_mult", "essential_exp_mult", "invest_mult", "property_mult",
                  "debt_service_mult", "liability_mult"]}
        stress_metrics = compute_metrics(
            st.session_state.household, st.session_state.cashflow, shock
        )

        # 对比表
        rows = [
            ("LIM", "流动性月数",
             f"{metrics.get('LIM',0):.1f} 月" if metrics.get('LIM') else "—",
             f"{stress_metrics.get('LIM',0):.1f} 月" if stress_metrics.get('LIM') else "—"),
            ("净值", "净值",
             hkd_short(metrics.get('E', 0)),
             hkd_short(stress_metrics.get('E', 0))),
            ("DSTI", "DSTI",
             f"{metrics.get('DSTI',0):.0%}" if metrics.get('DSTI') and metrics.get('DSTI') != float('inf') else "—",
             f"{stress_metrics.get('DSTI',0):.0%}" if stress_metrics.get('DSTI') and stress_metrics.get('DSTI') != float('inf') else "—"),
        ]

        # 表格：基准 vs 压力后
        table_html = '<table class="hf-compare-table"><thead><tr><th>基准</th><th>LIM</th><th>净值</th><th>DSTI</th></tr></thead><tbody>'
        base_row = f"<tr><td>基准</td><td>{rows[0][2]}</td><td>{rows[1][2]}</td><td>{rows[2][2]}</td></tr>"
        stress_row = f"<tr><td>压力后</td><td>{rows[0][3]}</td><td>{rows[1][3]}</td><td>{rows[2][3]}</td></tr>"
        table_html += base_row + stress_row + "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

        # 底部提示 — 用 unemployment.gap3 / gap6 准确区分 3月 vs 6月 缺口
        # 注：先提取 TOKEN 值到变量，避免 f-string 花括号里出现反斜杠转义（Python 3.11 语法限制）
        _yellow = TOKEN["yellow"]
        unemp = stress_metrics.get("unemployment", {})
        gap3 = unemp.get("gap3", 0)
        gap6 = unemp.get("gap6", 0)
        if gap3 or gap6:
            parts = []
            if gap3 == 0:
                parts.append("高流动性资产可覆盖 <b style='color:#3FB950'>全部 3 个月</b>必要支出，无缺口")
            else:
                parts.append(f"3 个月必要支出缺口约为 <b style='color:{_yellow}'>{hkd_short(gap3)}</b>")
            if gap6 > 0:
                parts.append(f"6 个月应急金缺口扩大至 {hkd_short(gap6)}")
            st.markdown(
                f'<div style="font-size:12.5px;color:{TOKEN["text_secondary"]};margin-top:10px">'
                f'<b style="color:{TOKEN["text_primary"]}">失业情景下：</b>' +
                "，".join(parts) + "。"
                f'</div>',
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    render_overview_page()
