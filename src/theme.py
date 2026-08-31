"""
全局主题与可复用组件库
参考 docs/mock-ui/ 原型图设计 token
"""

import streamlit as st
from typing import Dict, Any, List, Optional


# ============ 设计 Token ============

TOKEN = {
    # 背景
    "bg_deep": "#0B1120",        # 最深背景
    "bg_page": "#0F1628",        # 页面背景
    "bg_card": "#131C32",        # 卡片背景
    "bg_card_alt": "#182238",    # 备选卡片
    "bg_elev": "#1C2740",       # 悬浮层
    # 边框
    "border": "rgba(255,255,255,0.08)",
    "border_strong": "rgba(255,255,255,0.15)",
    # 文字
    "text_primary": "#E6EDF3",
    "text_secondary": "#8B949E",
    "text_muted": "#5A6474",
    # 状态色
    "green": "#3FB950",
    "green_bg": "rgba(63,185,80,0.15)",
    "yellow": "#F0B429",
    "yellow_bg": "rgba(240,180,41,0.15)",
    "red": "#F85149",
    "red_bg": "rgba(248,81,73,0.15)",
    # 品牌蓝
    "blue": "#2F81F7",
    "blue_bg": "rgba(47,129,247,0.15)",
    # 圆角与阴影
    "radius": "10px",
    "radius_sm": "6px",
    "shadow": "0 1px 2px rgba(0,0,0,0.3), 0 4px 12px rgba(0,0,0,0.25)",
}

LIGHT_TOKEN = {
    "green": "🟢",
    "yellow": "🟡",
    "red": "🔴",
}

STATUS_MAP = {
    "green": ("绿灯", TOKEN["green"], TOKEN["green_bg"]),
    "yellow": ("黄灯", TOKEN["yellow"], TOKEN["yellow_bg"]),
    "red": ("红灯", TOKEN["red"], TOKEN["red_bg"]),
}


# ============ 全局 CSS ============

def inject_css():
    """注入全局深色仪表盘样式"""
    st.markdown(f"""
    <style>
    /* ===== 根背景 ===== */
    .stApp {{
        background: {TOKEN['bg_deep']} !important;
    }}
    .appview-container .main .block-container {{
        background: {TOKEN['bg_page']};
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }}

    /* ===== 隐藏默认顶栏和菜单 ===== */
    header[data-testid="stHeader"] {{
        background: {TOKEN['bg_deep']} !important;
    }}
    header[data-testid="stHeader"] > div:first-child {{
        background: transparent;
    }}
    #MainMenu, footer, header {{visibility: hidden;}}

    /* ===== 侧栏 ===== */
    section[data-testid="stSidebar"] {{
        background: {TOKEN['bg_deep']} !important;
        border-right: 1px solid {TOKEN['border']};
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 1.5rem;
    }}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {TOKEN['text_primary']} !important;
    }}

    /* ===== 卡片容器 ===== */
    .hf-card {{
        background: {TOKEN['bg_card']};
        border: 1px solid {TOKEN['border']};
        border-radius: {TOKEN['radius']};
        padding: 18px 20px;
        box-shadow: {TOKEN['shadow']};
        margin-bottom: 14px;
    }}
    .hf-card-title {{
        color: {TOKEN['text_secondary']};
        font-size: 13px;
        font-weight: 500;
        letter-spacing: 0.3px;
        margin-bottom: 10px;
    }}

    /* ===== 指标卡片 ===== */
    .hf-metric {{
        background: {TOKEN['bg_card']};
        border: 1px solid {TOKEN['border']};
        border-radius: {TOKEN['radius']};
        padding: 16px 18px;
        box-shadow: {TOKEN['shadow']};
        height: 100%;
    }}
    .hf-metric-label {{
        font-size: 12px;
        color: {TOKEN['text_secondary']};
        font-weight: 500;
        margin-bottom: 6px;
        letter-spacing: 0.2px;
    }}
    .hf-metric-value {{
        font-size: 24px;
        font-weight: 600;
        color: {TOKEN['text_primary']};
        font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
        letter-spacing: -0.5px;
    }}
    .hf-metric-desc {{
        font-size: 11px;
        color: {TOKEN['text_muted']};
        margin-top: 5px;
        line-height: 1.4;
    }}
    .hf-metric-good {{ color: {TOKEN['green']}; }}
    .hf-metric-warn {{ color: {TOKEN['yellow']}; }}
    .hf-metric-bad  {{ color: {TOKEN['red']}; }}
    .hf-metric-neutral {{ color: {TOKEN['blue']}; }}

    /* ===== 告警卡片 ===== */
    .hf-alert {{
        background: {TOKEN['bg_card']};
        border: 1px solid {TOKEN['border']};
        border-left: 3px solid {TOKEN['yellow']};
        border-radius: {TOKEN['radius_sm']};
        padding: 12px 16px;
        margin-bottom: 10px;
    }}
    .hf-alert-yellow {{ border-left-color: {TOKEN['yellow']}; }}
    .hf-alert-red    {{ border-left-color: {TOKEN['red']}; }}
    .hf-alert-green  {{ border-left-color: {TOKEN['green']}; }}
    .hf-alert-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }}
    .hf-pill {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }}
    .hf-pill-yellow {{ background: {TOKEN['yellow_bg']}; color: {TOKEN['yellow']}; }}
    .hf-pill-red    {{ background: {TOKEN['red_bg']};    color: {TOKEN['red']}; }}
    .hf-pill-green  {{ background: {TOKEN['green_bg']};  color: {TOKEN['green']}; }}
    .hf-pill-blue   {{ background: {TOKEN['blue_bg']};   color: {TOKEN['blue']}; }}
    .hf-alert-title {{
        font-size: 14px;
        font-weight: 600;
        color: {TOKEN['text_primary']};
    }}
    .hf-alert-body {{
        font-size: 12.5px;
        color: {TOKEN['text_secondary']};
        line-height: 1.55;
    }}
    .hf-alert-body .val-highlight {{ color: {TOKEN['text_primary']}; font-weight: 500; }}
    .hf-alert-body .target {{ color: {TOKEN['text_muted']}; }}

    /* ===== 顶部 Header ===== */
    .hf-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 14px 0 16px 0;
        border-bottom: 1px solid {TOKEN['border']};
        margin-bottom: 18px;
    }}
    .hf-header-title {{
        font-size: 22px;
        font-weight: 600;
        color: {TOKEN['text_primary']};
        letter-spacing: -0.5px;
        margin: 0 0 4px 0;
    }}
    .hf-header-sub {{
        font-size: 13px;
        color: {TOKEN['text_secondary']};
        margin: 0;
    }}
    .hf-header-right {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }}
    .hf-header-chip {{
        background: {TOKEN['bg_card']};
        border: 1px solid {TOKEN['border']};
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 12px;
        color: {TOKEN['text_secondary']};
    }}
    .hf-header-chip b {{ color: {TOKEN['text_primary']}; font-weight: 600; }}

    /* ===== 按钮 ===== */
    .hf-btn {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: {TOKEN['bg_card_alt']};
        border: 1px solid {TOKEN['border_strong']};
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 500;
        color: {TOKEN['text_primary']};
        cursor: pointer;
        text-decoration: none;
        transition: all 0.15s;
    }}
    .hf-btn:hover {{ background: {TOKEN['bg_elev']}; }}
    .hf-btn-primary {{
        background: {TOKEN['blue']};
        border-color: {TOKEN['blue']};
        color: white;
    }}
    .hf-btn-primary:hover {{ background: #4090F7; }}

    /* ===== 综合风险总卡 ===== */
    .hf-overview-card {{
        background: {TOKEN['bg_card']};
        border: 1px solid {TOKEN['border']};
        border-radius: {TOKEN['radius']};
        padding: 28px 32px;
        margin-bottom: 16px;
        position: relative;
        overflow: hidden;
    }}
    .hf-overview-card::before {{
        content: '';
        position: absolute;
        top: -40px; right: -40px;
        width: 200px; height: 200px;
        background: radial-gradient(circle, {TOKEN['yellow_bg']} 0%, transparent 70%);
        pointer-events: none;
    }}
    .hf-big-light {{
        font-size: 48px;
        font-weight: 700;
        letter-spacing: -1px;
        line-height: 1;
        margin-bottom: 12px;
    }}
    .hf-big-light.yellow {{ color: {TOKEN['yellow']}; }}
    .hf-big-light.green {{ color: {TOKEN['green']}; }}
    .hf-big-light.red   {{ color: {TOKEN['red']}; }}
    .hf-overview-desc {{
        font-size: 14px;
        color: {TOKEN['text_secondary']};
        line-height: 1.7;
        max-width: 600px;
        margin-bottom: 18px;
    }}
    .hf-overview-actions {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
    }}

    /* ===== 表格深色化 ===== */
    .hf-table {{
        width: 100%;
        border-collapse: collapse;
        background: {TOKEN['bg_card']};
        border: 1px solid {TOKEN['border']};
        border-radius: {TOKEN['radius']};
        overflow: hidden;
        font-size: 13px;
    }}
    .hf-table thead tr {{
        background: {TOKEN['bg_elev']};
        color: {TOKEN['text_secondary']};
        font-size: 11.5px;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }}
    .hf-table th, .hf-table td {{
        padding: 10px 14px;
        text-align: left;
        border-bottom: 1px solid {TOKEN['border']};
    }}
    .hf-table tbody tr:last-child td {{ border-bottom: none; }}
    .hf-table tbody tr:hover {{ background: {TOKEN['bg_elev']}; }}
    .hf-table td {{ color: {TOKEN['text_primary']}; }}

    /* ===== 深色 Plotly 容器 ===== */
    .js-plotly-plot .plotly .main-svg {{
        background: transparent !important;
    }}
    .js-plotly-plot {{
        background: transparent !important;
        border-radius: {TOKEN['radius']};
    }}

    /* ===== 情景对比小表 ===== */
    .hf-compare-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 13px;
    }}
    .hf-compare-table th, .hf-compare-table td {{
        padding: 12px 14px;
        text-align: left;
    }}
    .hf-compare-table thead th {{
        color: {TOKEN['text_muted']};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        border-bottom: 1px solid {TOKEN['border']};
    }}
    .hf-compare-table tbody td {{
        color: {TOKEN['text_primary']};
        border-bottom: 1px solid {TOKEN['border']};
    }}
    .hf-compare-table td:first-child {{
        color: {TOKEN['text_secondary']};
        font-weight: 500;
    }}

    /* ===== Streamlit 组件深色化 ===== */
    div[data-testid="stMetric"] {{
        background: {TOKEN['bg_card']};
        border: 1px solid {TOKEN['border']};
        border-radius: {TOKEN['radius']};
        padding: 14px 18px;
    }}
    div[data-testid="stMetric"] label {{
        color: {TOKEN['text_secondary']} !important;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {TOKEN['text_primary']} !important;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
        color: {TOKEN['text_secondary']} !important;
    }}
    div[data-testid="stSelectbox"] > div > div > div {{
        background: {TOKEN['bg_card']} !important;
        border: 1px solid {TOKEN['border']} !important;
        color: {TOKEN['text_primary']} !important;
    }}
    div[data-testid="stCheckbox"] label,
    div[data-testid="stRadio"] label {{
        color: {TOKEN['text_primary']} !important;
    }}
    hr, .stMarkdown hr {{
        background: {TOKEN['border']} !important;
        border-color: {TOKEN['border']} !important;
    }}
    div.stAlert {{
        border-radius: {TOKEN['radius_sm']};
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        background: {TOKEN['bg_card']};
        padding: 4px;
        border-radius: {TOKEN['radius_sm']};
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {TOKEN['text_secondary']};
        border-radius: 6px;
    }}
    .stTabs [aria-selected="true"] {{
        background: {TOKEN['bg_elev']};
        color: {TOKEN['text_primary']} !important;
    }}

    /* ===== 侧边栏导航项 ===== */
    .hf-nav-item {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 9px 12px;
        border-radius: 8px;
        color: {TOKEN['text_secondary']};
        font-size: 14px;
        cursor: pointer;
        text-decoration: none;
        transition: background 0.15s;
        margin-bottom: 2px;
    }}
    .hf-nav-item:hover {{ background: {TOKEN['bg_elev']}; color: {TOKEN['text_primary']}; }}
    .hf-nav-item.active {{
        background: {TOKEN['blue_bg']};
        color: {TOKEN['blue']};
        font-weight: 500;
    }}
    .hf-nav-dot {{
        width: 6px; height: 6px;
        border-radius: 50%;
        background: currentColor;
        flex-shrink: 0;
    }}

    /* ===== 侧边栏 st.button → 看起来像导航项 ===== */
    section[data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 9px 12px;
        border-radius: 8px;
        color: {TOKEN['text_secondary']};
        font-size: 14px;
        font-weight: 400;
        background: transparent;
        border: none;
        justify-content: flex-start;
        margin-bottom: 2px;
        height: auto;
        min-height: 36px;
        line-height: 1.3;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: {TOKEN['bg_elev']};
        color: {TOKEN['text_primary']};
        border: none;
    }}
    section[data-testid="stSidebar"] .stButton.active > button,
    section[data-testid="stSidebar"] .stButton > button.active {{
        background: {TOKEN['blue_bg']} !important;
        color: {TOKEN['blue']} !important;
        font-weight: 500;
        border: none;
    }}

    /* ===== 主页面 st.button → hf-btn 风格 ===== */
    .stButton > button.hf-btn-primary,
    button.hf-btn-primary {{
        background: {TOKEN['blue']} !important;
        color: #fff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 6px 16px !important;
        font-size: 12.5px !important;
        font-weight: 500 !important;
        height: auto !important;
        min-height: 36px !important;
    }}
    .stButton > button.hf-btn-primary:hover {{
        background: #4193ff !important;
        color: #fff !important;
    }}
    button.hf-btn-secondary {{
        background: {TOKEN['bg_elev']} !important;
        color: {TOKEN['text_primary']} !important;
        border: 1px solid {TOKEN['border']} !important;
        border-radius: 6px !important;
        padding: 6px 16px !important;
        font-size: 12.5px !important;
        height: auto !important;
        min-height: 36px !important;
    }}
    .stButton > button.hf-btn-secondary:hover {{
        background: {TOKEN['bg_card_alt']} !important;
        border-color: {TOKEN['blue']} !important;
    }}

    /* ===== 章节标题 ===== */
    .hf-section {{
        font-size: 15px;
        font-weight: 600;
        color: {TOKEN['text_primary']};
        margin: 6px 0 12px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    .hf-section::before {{
        content: '';
        width: 3px; height: 16px;
        background: {TOKEN['blue']};
        border-radius: 2px;
    }}

    /* ===== 分类汇总/小组件卡片 ===== */
    .hf-sub-card {{
        background: {TOKEN['bg_card']};
        border: 1px solid {TOKEN['border']};
        border-radius: {TOKEN['radius_sm']};
        padding: 14px 16px;
    }}
    .hf-sub-label {{
        font-size: 11.5px;
        color: {TOKEN['text_secondary']};
        font-weight: 500;
        letter-spacing: 0.3px;
        margin-bottom: 4px;
    }}
    .hf-sub-value {{
        font-size: 20px;
        font-weight: 600;
        color: {TOKEN['text_primary']};
        font-family: -apple-system, "Segoe UI", sans-serif;
    }}
    .hf-sub-desc {{
        font-size: 11px;
        color: {TOKEN['text_muted']};
        margin-top: 4px;
    }}

    /* ===== 突破清单项 ===== */
    .hf-breach-item {{
        background: {TOKEN['bg_card']};
        border: 1px solid {TOKEN['border']};
        border-radius: {TOKEN['radius_sm']};
        padding: 14px 16px;
        margin-bottom: 8px;
    }}
    .hf-breach-num {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px; height: 22px;
        border-radius: 50%;
        background: {TOKEN['red_bg']};
        color: {TOKEN['red']};
        font-size: 12px;
        font-weight: 700;
        margin-right: 8px;
    }}

    /* 隐藏 Streamlit 自动导航 */
    section[data-testid="stSidebar"] > div > div:first-child > div:first-child {{
        display: none;
    }}
    div[data-testid="stSidebarNav"] {{
        display: none !important;
    }}

    /* 隐藏 Streamlit 顶部 header + hamburger + decoration + footer */
    header[data-testid="stHeader"] {{
        display: none !important;
    }}
    div[data-testid="stDecoration"] {{
        display: none !important;
    }}
    #MainMenu {{
        visibility: hidden !important;
    }}
    footer {{
        display: none !important;
    }}

    /* 侧边栏：让内容可滚动且不留多余空间 */
    section[data-testid="stSidebar"] {{
        padding-top: 1rem !important;
    }}
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 0.5rem !important;
        padding-bottom: 1rem !important;
        max-height: calc(100vh - 2rem) !important;
        overflow-y: auto !important;
    }}
    section[data-testid="stSidebar"] .block-container > div:first-child {{
        margin-top: 0 !important;
    }}
    </style>
    """, unsafe_allow_html=True)


# ============ Plotly 深色布局 ============

def dark_plotly_layout(fig, height=320):
    """应用深色主题到 Plotly 图表"""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TOKEN["text_primary"], size=12),
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        legend=dict(
            font=dict(color=TOKEN["text_secondary"], size=11),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
        ),
    )
    fig.update_xaxes(
        gridcolor=TOKEN["border"],
        linecolor=TOKEN["border"],
        tickcolor=TOKEN["border"],
        tickfont=dict(color=TOKEN["text_secondary"]),
    )
    fig.update_yaxes(
        gridcolor=TOKEN["border"],
        linecolor=TOKEN["border"],
        tickcolor=TOKEN["border"],
        tickfont=dict(color=TOKEN["text_secondary"]),
    )
    return fig


# ============ 可复用组件 ============

def header(title: str, subtitle: str, as_of: str = "", chips: List[Dict] = None):
    """
    页面顶部 Header
    chips: [{"label": "汇率日期", "value": "2026-08-28"}, ...]
    """
    chips_html = ""
    if chips:
        for c in chips:
            chips_html += f'<div class="hf-header-chip">{c["label"]}<br><b>{c["value"]}</b></div>'
    light_dot = ""
    html = f"""
    <div class="hf-header">
        <div>
            <h1 class="hf-header-title">{title}</h1>
            <p class="hf-header-sub">{subtitle}</p>
        </div>
        <div class="hf-header-right">
            {chips_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def metric_card(label: str, value: str, desc: str = "", tone: str = "neutral"):
    """
    指标卡片
    tone: good / warn / bad / neutral
    """
    tone_class = {"good": "hf-metric-good", "warn": "hf-metric-warn", "bad": "hf-metric-bad", "neutral": "hf-metric-neutral"}.get(tone, "")
    desc_html = f'<div class="hf-metric-desc">{desc}</div>' if desc else ""
    html = f"""
    <div class="hf-metric">
        <div class="hf-metric-label">{label}</div>
        <div class="hf-metric-value {tone_class}">{value}</div>
        {desc_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def alert_card(status: str, title: str, body: str):
    """
    告警卡片
    status: green / yellow / red
    body 中的 {current} / {target} 会被高亮
    """
    pill_text, pill_color, border_color = STATUS_MAP.get(status, STATUS_MAP["green"])
    border_map = {"green": "hf-alert-green", "yellow": "hf-alert-yellow", "red": "hf-alert-red"}
    body_formatted = body.replace("{", "<span class='val-highlight'>").replace("}", "</span>")
    html = f"""
    <div class="hf-alert {border_map.get(status, '')}" style="border-left-color: {pill_color}">
        <div class="hf-alert-header">
            <span class="hf-pill hf-pill-{status}">{pill_text}</span>
            <span class="hf-alert-title">{title}</span>
        </div>
        <div class="hf-alert-body">{body_formatted}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def overview_big_light(status: str, description: str, actions_html: str = ""):
    """综合风险大卡 + 巨大灯号"""
    _, light_color, _ = STATUS_MAP.get(status, STATUS_MAP["green"])
    light_text = STATUS_MAP.get(status, STATUS_MAP["green"])[0]
    html = f"""
    <div class="hf-overview-card">
        <div class="hf-big-light {status}">{light_text}</div>
        <div class="hf-overview-desc">{description}</div>
        <div class="hf-overview-actions">{actions_html}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def sub_card(label: str, value: str, desc: str = ""):
    """小组件卡片（分类汇总用）"""
    desc_html = f'<div class="hf-sub-desc">{desc}</div>' if desc else ""
    html = f"""
    <div class="hf-sub-card">
        <div class="hf-sub-label">{label}</div>
        <div class="hf-sub-value">{value}</div>
        {desc_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def section_title(title: str, right_html: str = ""):
    """章节标题"""
    right = f'<div style="margin-left:auto">{right_html}</div>' if right_html else ""
    html = f'<div class="hf-section">{title} {right}</div>'
    st.markdown(html, unsafe_allow_html=True)


def pill(text: str, status: str = "green"):
    """状态标签"""
    _, color, _ = STATUS_MAP.get(status, STATUS_MAP["green"])
    html = f'<span class="hf-pill hf-pill-{status}">{text}</span>'
    st.markdown(html, unsafe_allow_html=True)
    return html


def action_btn(label: str, kind: str = "secondary", on_click=None, args=None, key: str = None) -> bool:
    """
    主页面操作按钮（真实可点击的 st.button，带 hf-btn 风格）
    kind: "primary" = 蓝底白字, "secondary" = 深色描边
    返回: st.button 的返回值（True 表示刚被点击）
    """
    import streamlit.components.v1 as components
    cls = "hf-btn-primary" if kind == "primary" else "hf-btn-secondary"
    clicked = st.button(
        label,
        key=key or f"action_btn_{label}",
        on_click=on_click,
        args=args,
        type="secondary",
        use_container_width=False,
    )
    # 注入 JS 给按钮加上自定义 class（Streamlit button 的 type 参数不够精细）
    components.html(f"""
    <script>
        // 给最近一个被渲染的 action button 加自定义 class
        document.querySelectorAll('.stButton > button').forEach(btn => {{
            if (btn.textContent.trim() === '{label}' && !btn.classList.contains('hf-btn-primary') && !btn.classList.contains('hf-btn-secondary')) {{
                btn.classList.add('{cls}');
            }}
        }});
    </script>
    """, height=0)
    return clicked


def _set_page(page_key: str):
    """st.button on_click 回调：切换当前页面"""
    st.session_state.current_page = page_key


# ============ 侧边栏定制 ============

def custom_sidebar(data_mode: str, as_of: str, overall_light: str, pages: List[Dict]):
    """
    自定义深色侧边栏 — 用 st.button 导航，全在同一页面内切换
    pages: [{"label": "总览", "page_key": "overview", "active": True}, ...]
    """
    current = st.session_state.get("current_page", "overview")

    with st.sidebar:
        # Logo + 标题
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;padding:4px 0">
            <div style="width:38px;height:38px;border-radius:10px;background:{TOKEN['blue']};
                        display:flex;align-items:center;justify-content:center;
                        font-weight:700;font-size:16px;color:white;letter-spacing:-0.5px">HF</div>
            <div>
                <div style="color:{TOKEN['text_primary']};font-size:14px;font-weight:600">家庭财务风险驾驶舱</div>
                <div style="color:{TOKEN['text_muted']};font-size:11px;letter-spacing:0.3px">Household Financial Risk Desk</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 导航标题
        st.markdown(
            f'<div style="color:{TOKEN["text_muted"]};font-size:11px;letter-spacing:0.5px;margin-bottom:8px;margin-top:10px">主导航</div>',
            unsafe_allow_html=True,
        )

        # 用 st.button 实现导航（在同一页面内切换）
        for p in pages:
            page_key = p.get("page_key", p.get("link", ""))
            is_active = (current == page_key)
            icon = p.get("icon", "●")
            btn_label = f"{icon}  {p['label']}"

            # 每个导航按钮：on_click 切换 page，然后通过 CSS 给当前激活项加 active class
            # Streamlit button 按 label 去重，所以要保持 label 唯一
            st.button(
                btn_label,
                key=f"nav_{page_key}",
                on_click=_set_page,
                args=(page_key,),
                use_container_width=True,
            )
            if is_active:
                st.markdown(f"""
                <script>
                    // 给刚渲染的这个 button 加上 active 类
                    document.querySelectorAll('section[data-testid="stSidebar"] .stButton > button').forEach(btn => {{
                        if (btn.textContent.includes('{icon}') && btn.textContent.includes('{p["label"]}')) {{
                            btn.classList.add('active');
                        }}
                    }});
                </script>
                """, unsafe_allow_html=True)

        # 分隔
        st.markdown(
            f'<div style="border-top:1px solid {TOKEN["border"]};margin:14px 0 10px"></div>',
            unsafe_allow_html=True,
        )

        # 当前数据模式卡
        st.markdown(f"""
        <div class="hf-card" style="padding:14px 16px;margin-bottom:12px">
            <div class="hf-card-title">当前数据模式</div>
            <div style="font-size:16px;font-weight:600;color:{TOKEN['text_primary']};margin-bottom:4px">
                { 'Demo 家庭' if data_mode == 'demo' else '本地数据' }
            </div>
            <div style="font-size:11.5px;color:{TOKEN['text_secondary']};line-height:1.5;margin-bottom:10px">
                演示数据已加载，可直接呈现黄灯、联合压力与建议路径。
            </div>
            <div class="hf-status-chip" style="display:inline-flex;background:{TOKEN['bg_elev']};
                     color:{TOKEN['text_secondary']};padding:4px 10px;border-radius:6px;font-size:11px">
                汇率 {as_of}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 风险循环
        st.markdown(f"""
        <details class="hf-card" style="padding:14px 16px;margin-bottom:12px;cursor:pointer">
            <summary style="list-style:none;cursor:pointer;font-size:13px;font-weight:600;color:{TOKEN['text_primary']};
                            display:flex;justify-content:space-between;align-items:center;margin:-14px -16px 0 -16px;padding:14px 16px">
                <span style="display:flex;align-items:center;gap:8px">
                    <span style="width:6px;height:6px;border-radius:50%;background:{TOKEN['blue']}"></span>
                    风险循环
                </span>
                <span style="color:{TOKEN['text_muted']};font-size:11px">▾</span>
            </summary>
            <div style="margin-top:12px">
                <div class="hf-nav-item"><span class="hf-nav-dot"></span>定义风险</div>
                <div class="hf-nav-item"><span class="hf-nav-dot"></span>计量现状</div>
                <div class="hf-nav-item"><span class="hf-nav-dot"></span>设定限额</div>
                <div class="hf-nav-item"><span class="hf-nav-dot"></span>压力测试</div>
                <div class="hf-nav-item"><span class="hf-nav-dot"></span>处置建议</div>
            </div>
        </details>
        """, unsafe_allow_html=True)

        # 底部免责
        st.markdown(f"""
        <div style="font-size:10.5px;color:{TOKEN['text_muted']};line-height:1.6;
                    border-top:1px solid {TOKEN['border']};padding-top:12px;margin-top:8px">
            本产品用于个人风险管理与作品展示，不构成投资、信贷或税务建议。
            <br>当前展示为 Demo 数据
        </div>
        """, unsafe_allow_html=True)
