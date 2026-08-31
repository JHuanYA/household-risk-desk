/**
 * 图表封装 —— Plotly.js（CDN 加载，无需打包）
 * 命名空间: window.Charts
 */
(function (root) {
  "use strict";

  var PLOTLY_LAYOUT_BASE = {
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { color: "#8B949E", size: 12 },
    margin: { l: 0, r: 0, t: 0, b: 0 },
    showlegend: false,
  };

  // ============================================================
  // 资产结构饼图（环形）
  // ============================================================

  function assetPie(elId, catTotals, netValue) {
    var labels = [];
    var values = [];
    var colors = [];
    var colorMap = {
      cash: "#58A6FF",
      investment: "#3FB950",
      property: "#F0B429",
      other: "#8B949E",
    };
    var labelMap = {
      cash: "现金及等价",
      investment: "投资",
      property: "房产",
      other: "其他资产",
    };
    Object.keys(catTotals || {}).forEach(function (k) {
      var v = catTotals[k];
      if (v > 0) {
        labels.push(labelMap[k] || k);
        values.push(v);
        colors.push(colorMap[k] || "#8B949E");
      }
    });
    if (values.length === 0) {
      document.getElementById(elId).innerHTML = '<div class="hf-muted" style="padding:40px;text-align:center">暂无数据</div>';
      return;
    }
    var data = [{
      type: "pie",
      labels: labels,
      values: values,
      hole: 0.6,
      marker: { colors: colors, line: { color: "#161B22", width: 2 } },
      textfont: { color: "#E6EDF3", size: 11 },
      textinfo: "percent",
      hovertemplate: "<b>%{label}</b><br>HK$%{value:,.0f}<br>占比 %{percent}<extra></extra>",
    }];
    var layout = Object.assign({}, PLOTLY_LAYOUT_BASE, {
      height: 280,
      annotations: [{
        text: "净值<br><b style='font-size:18px;color:#E6EDF3'>HK$" + (netValue || 0).toLocaleString() + "</b>",
        x: 0.5, y: 0.5, showarrow: false, align: "center",
        font: { size: 11, color: "#8B949E" },
      }],
      showlegend: true,
      legend: { orientation: "h", yanchor: "top", y: -0.08, xanchor: "center", x: 0.5, font: { size: 10.5, color: "#8B949E" } },
    });
    Plotly.purge(elId);
    Plotly.newPlot(elId, data, layout, { displayModeBar: false, responsive: true });
  }

  // ============================================================
  // 收入/支出结构条
  // ============================================================

  function cfBar(elId, cfRows) {
    var inc = [];
    var out = [];
    (cfRows || []).forEach(function (r) {
      if (r.direction === "in") inc.push({ name: r.name, v: r.hkd });
      else if (r.direction === "out") out.push({ name: r.name, v: r.hkd });
    });

    var data = [
      { type: "bar", x: inc.map(function (r) { return r.name; }), y: inc.map(function (r) { return r.v; }),
        name: "收入", marker: { color: "#3FB950" } },
      { type: "bar", x: out.map(function (r) { return r.name; }), y: out.map(function (r) { return -r.v; }),
        name: "支出", marker: { color: "#F85149" } },
    ];
    var layout = Object.assign({}, PLOTLY_LAYOUT_BASE, {
      height: 260,
      barmode: "group",
      yaxis: { tickprefix: "HK$", hoverformat: ",.0f" },
      showlegend: true,
      legend: { orientation: "h", yanchor: "top", y: -0.05, xanchor: "center", x: 0.5 },
    });
    Plotly.purge(elId);
    Plotly.newPlot(elId, data, layout, { displayModeBar: false, responsive: true });
  }

  // ============================================================
  // 多情景对比条形图（核心指标变化）
  // 改为水平条形图：Y 轴是指标名称，X 轴是 HKD 金额
  // 解决 Dashboard 窄栏里长标签被截断的问题
  // ============================================================

  // 图表专用短名（完整名仍保留在 compare 表格里）
  var SHORT_NAMES = {
    "净值": "净值 E",
    "资产": "总资产",
    "负债": "总负债",
    "高流动性资产": "高流动资产",
    "应急金缺口": "应急缺口",
  };

  function stressCompareBar(elId, compare) {
    var items = (compare.comparison || []).filter(function (c) { return c.unit === "HKD"; });
    if (items.length === 0) { document.getElementById(elId).innerHTML = ""; return; }
    var names = items.map(function (c) { return SHORT_NAMES[c.name] || c.name; });
    var baseVals = items.map(function (c) { return c.baseline || 0; });
    var stressVals = items.map(function (c) { return c.stress || 0; });

    var data = [
      { type: "bar", y: names, x: baseVals, name: "基准",
        marker: { color: "#30363D", line: { width: 0 } },
        orientation: "h",
        hovertemplate: "<b>基准</b><br>%{y}<br>HK$%{x:,.0f}<extra></extra>" },
      { type: "bar", y: names, x: stressVals, name: "压力",
        marker: { color: "#58A6FF", line: { width: 0 } },
        orientation: "h",
        hovertemplate: "<b>压力</b><br>%{y}<br>HK$%{x:,.0f}<extra></extra>" },
    ];
    var layout = Object.assign({}, PLOTLY_LAYOUT_BASE, {
      height: Math.max(200, items.length * 42 + 50),  // 按行数自适应，每行 ~42px
      barmode: "group",
      bargap: 0.3,
      bargroupgap: 0.15,
      yaxis: {
        automargin: true,   // 让 Plotly 自动为左侧标签留边
        tickfont: { size: 11, color: "#E6EDF3" },
        autorange: "reversed",  // 让第一项显示在顶部
      },
      xaxis: {
        tickprefix: "HK$",
        hoverformat: ",.0f",
        tickfont: { size: 10, color: "#8B949E" },
        gridcolor: "rgba(48, 54, 61, 0.5)",
        showgrid: true,
      },
      margin: { l: 10, r: 8, t: 4, b: 4 },  // 紧凑，yaxis automargin 会接管
      showlegend: true,
      legend: { orientation: "h", yanchor: "top", y: -0.02, xanchor: "center", x: 0.5, font: { size: 10.5 } },
    });
    Plotly.purge(elId);
    Plotly.newPlot(elId, data, layout, { displayModeBar: false, responsive: true });
  }

  root.Charts = {
    assetPie: assetPie,
    cfBar: cfBar,
    stressCompareBar: stressCompareBar,
  };
})(typeof window !== "undefined" ? window : globalThis);
