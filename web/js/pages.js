/**
 * 页面渲染函数 —— 6 页 SPA
 * 命名空间: window.Pages
 *
 * 每个 render 函数:
 *   1. 读 App.current 数据
 *   2. 生成 HTML 字符串并塞到对应 page div
 *   3. 绑定事件（editable table, Plotly, 按钮）
 */
(function (root) {
  "use strict";

  var App = root.App;
  var Engine = root.Engine;
  var UI = root.UI;
  var Charts = root.Charts;

  function $(id) { return document.getElementById(id); }

  // ============================================================
  // 辅助：当 metrics 为 null 时显示拦截横幅
  // ============================================================
  function _guardNoData(state, pageId) {
    if (!state.metrics) {
      var html = '<div class="hf-banner hf-banner-error">' +
        '<div class="hf-banner-title">⚠ 无法计算风险指标</div>' +
        '<div class="hf-error-item">可能原因：汇率表无效 / 无收入行 / 引擎运行时错误</div>' +
        '<div class="hf-error-item">请前往 <a href="#data" style="color:inherit;text-decoration:underline">数据输入</a> 修正后刷新</div>' +
        '</div>';
      $(pageId).innerHTML = html;
      return true;
    }
    return false;
  }

  // ============================================================
  // 0. Dashboard —— 总览
  // ============================================================

  function renderDashboard() {
    var state = App.current;
    if (_guardNoData(state, "page-dashboard")) return;
    var m = state.metrics;
    var lim = state.limits;
    var overall = lim.overall;
    var alerts = lim.alerts;
    var color = UI.statusColor(overall);

    var html = "";

    // 顶部大卡：综合灯
    var desc = "核心指标均在安全区内";
    if (overall === "red") desc = "关键指标已击穿红线，建议立即处置";
    else if (overall === "yellow") desc = "流动性缓冲不足，集中度偏高";

    html += '<div class="hf-big-light">' +
      '<div class="hf-big-light-dot" style="background:' + color + ';color:' + color + '"></div>' +
      '<div class="hf-big-light-body">' +
      '<h2>家庭风险态势总览</h2>' +
      '<p>' + desc + '</p>' +
      '<div class="hf-big-light-tags">' +
      UI.lightPill(overall, UI.statusLabel(overall)) +
      '<span class="hf-pill">Demo 家庭</span>' +
      '<span class="hf-pill" style="border-color:' + (alerts.length ? UI.STATUS_COLORS.yellow : UI.STATUS_COLORS.green) + ';color:' + (alerts.length ? UI.STATUS_COLORS.yellow : UI.STATUS_COLORS.green) + '">' + alerts.length + ' 项预警</span>' +
      '</div>' +
      '</div></div>';

    // 4 张指标卡
    var lev = m.LEV;
    var levWarn = isFinite(lev) && lev > 0.4;
    var lim = m.LIM;
    var limWarn = lim != null && lim < 6;
    var limBad = lim != null && lim < 3;
    var gap = m.GAP;
    var dsti = m.DSTI;
    var dstiWarn = isFinite(dsti) && dsti > 0.4;

    html += '<div class="hf-row">' +
      UI.metricCard("净值 E", UI.hkdShort(m.E), "压力后仍为正", "neutral") +
      UI.metricCard("杠杆 L/A", UI.pct(lev), levWarn ? "高于目标 40%" : "在目标内", levWarn ? "warn" : "good") +
      UI.metricCard("流动性月数 LIM", lim != null ? UI.months(lim) : "N/A", limBad ? "跌破安全线" : limWarn ? "低于目标 6 月" : "达标", limBad ? "bad" : limWarn ? "warn" : "good") +
      UI.metricCard("应急金缺口 GAP", gap != null ? UI.hkdShort(gap) : "N/A", gap && gap > 0 ? "补足后可回到限额内" : "无缺口", gap && gap > 0 ? "warn" : "good") +
      '</div>';

    // 下一行：DSTI + 空 + 资产饼图
    html += '<div class="hf-split hf-split-3-2" style="margin-top:16px">' +
      '<div>' +
      UI.sectionTitle("非绿灯告警", '<span class="hf-pill" style="border-color:' + UI.STATUS_COLORS.yellow + ';color:' + UI.STATUS_COLORS.yellow + '">' + alerts.length + ' 项</span>') +
      (alerts.length ? alerts.map(function (a) { return UI.alertCard(a.status, a.name, a.reason); }).join("") :
        '<div class="hf-card" style="text-align:center;padding:24px;color:' + UI.STATUS_COLORS.green + '">✅ 所有风险指标均在限额内</div>') +
      '</div>' +
      '<div>' +
      UI.sectionTitle("资产结构", "以净值为分母观察集中度") +
      '<div class="hf-chart"><div id="pie-asset"></div></div>' +
      '</div>' +
      '</div>';

    // 压力预览
    var defaultSc = Engine.SCENARIOS.find(function (s) { return s.defaultSelected; }) || Engine.SCENARIOS[8];
    var stressMetrics = Engine.computeMetrics(
      Engine.applyFx(state.household, state.cashflow, state.fx).household,
      Engine.applyFx(state.household, state.cashflow, state.fx).cashflow,
      defaultSc
    );
    var stressLimits = Engine.checkAllLimits(stressMetrics);
    var cmp = Engine.compareScenarios(m, stressMetrics, lim, stressLimits);

    html += '<hr class="hf-divider">' +
      UI.sectionTitle("压力情景快捷预览", '默认: <b>' + defaultSc.name + '</b>') +
      '<div class="hf-split hf-split-3-2">' +
      '<div>' +
      '<table class="hf-compare-table"><thead><tr>' +
      '<th>指标</th><th>基准</th><th>压力后</th><th>变化</th>' +
      '</tr></thead><tbody>' +
      cmp.comparison.filter(function (c) { return c.unit !== "HKD" || c.key === "E" || c.key === "GAP"; }).map(function (c) {
        var diffClass = c.diff != null ? (c.diff > 0 ? "hf-diff-pos" : c.diff < 0 ? "hf-diff-neg" : "") : "";
        return '<tr><td>' + c.name + '</td><td>' + c.baseline_display + '</td><td>' + c.stress_display + '</td><td class="' + diffClass + '">' + c.diff_display + '</td></tr>';
      }).join("") +
      '</tbody></table>' +
      '</div>' +
      '<div>' +
      '<div class="hf-chart"><div id="pie-stress"></div></div>' +
      '</div>' +
      '</div>';

    // 底部失业提示
    var gap3 = stressMetrics.unemployment.gap3;
    var gap6 = stressMetrics.unemployment.gap6;
    var parts = [];
    if (gap3 === 0) parts.push("高流动性资产可覆盖 <b style='color:#3FB950'>全部 3 个月</b>必要支出");
    else parts.push("3 个月必要支出缺口约为 <b style='color:" + UI.STATUS_COLORS.yellow + "'>" + UI.hkdShort(gap3) + "</b>");
    if (gap6 > 0) parts.push("6 个月应急金缺口扩大至 " + UI.hkdShort(gap6));
    html += '<div style="font-size:12.5px;color:var(--text-secondary);margin-top:10px">' +
      '<b>失业情景下：</b>' + parts.join("，") + "。</div>";

    $("page-dashboard").innerHTML = html;

    // 饼图
    Charts.assetPie("pie-asset", m.catTotals, m.E);
    // 压力对比用 E/A/L 三个 HKD 指标的小柱图
    Charts.stressCompareBar("pie-stress", cmp);
  }

  // ============================================================
  // 1. Data Entry —— 独立数据输入页
  // ============================================================

  function renderDataEntry() {
    var state = App.current;
    var html = '<h1>数据输入</h1><p class="sub">编辑家庭资产负债、现金流和汇率设置。任何改动立即自动保存。</p>';

    // 校验错误横幅（数据输入页必须显示）
    html += UI.errorBanner(state.errors, "all");

    html += '<div class="hf-toolbar">' +
      '<button class="hf-btn hf-btn-secondary" id="btn-reset-demo">↺ 重置为 Demo 数据</button>' +
      '<span style="flex:1"></span>' +
      '<span class="hf-muted">数据自动保存到浏览器 localStorage</span>' +
      '</div>';

    // --- Household ---
    html += UI.sectionTitle("资产负债表 (household.csv)", "共 " + state.household.length + " 行");
    html += '<div id="table-household">' + UI.editableTable(
      "tbl-household", state.household, [
        { key: "name",          label: "名称",      type: "text",   width: "18%" },
        { key: "type",          label: "类型",      type: "select", width: "8%",  options: [{ value: "asset", label: "资产" }, { value: "liability", label: "负债" }] },
        { key: "category",      label: "类别",      type: "select", width: "10%", options: [
          { value: "cash",       label: "现金" },
          { value: "investment", label: "投资" },
          { value: "property",   label: "房产" },
          { value: "other",      label: "其他" },
          { value: "mortgage",   label: "按揭" },
          { value: "consumer",   label: "消费贷" },
        ]},
        { key: "amount",        label: "金额",      type: "number", width: "12%" },
        { key: "currency",      label: "币种",      type: "select", width: "8%",  options: [{ value: "HKD", label: "HKD" }, { value: "USD", label: "USD" }, { value: "CNY", label: "CNY" }] },
        { key: "liquidity",     label: "流动性",    type: "select", width: "10%", options: [{ value: "high", label: "高" }, { value: "medium", label: "中" }, { value: "low", label: "低" }, { value: "", label: "—" }] },
        { key: "owner",         label: "持有人",    type: "text",   width: "8%" },
        { key: "note",          label: "备注",      type: "text",   width: "16%" },
      ],
      function (copy) { App.setHousehold(copy); },
      null, null,
      state.errors.household  // 行级错误
    ) + '</div>';

    // --- Cashflow ---
    html += UI.sectionTitle("现金流 (cashflow.csv)", "共 " + state.cashflow.length + " 行");
    html += '<div id="table-cashflow">' + UI.editableTable(
      "tbl-cashflow", state.cashflow, [
        { key: "name",          label: "名称",      type: "text",   width: "18%" },
        { key: "direction",     label: "方向",      type: "select", width: "8%",  options: [{ value: "in", label: "收入" }, { value: "out", label: "支出" }] },
        { key: "monthly_amount",label: "月金额",    type: "number", width: "12%" },
        { key: "currency",      label: "币种",      type: "select", width: "8%",  options: [{ value: "HKD", label: "HKD" }, { value: "USD", label: "USD" }, { value: "CNY", label: "CNY" }] },
        { key: "essential",     label: "必要",      type: "checkbox", width: "6%" },
        { key: "debt_service", label: "债务供款",  type: "checkbox", width: "8%" },
        { key: "source_rank",   label: "收入优先级",type: "number", width: "10%", step: "1", placeholder: "空=支出" },
        { key: "note",          label: "备注",      type: "text",   width: "20%" },
      ],
      function (copy) { App.setCashflow(copy); },
      null, null,
      state.errors.cashflow  // 行级错误
    ) + '</div>';

    // --- FX ---
    html += UI.sectionTitle("汇率设置 (fx.csv)", "可编辑");
    var fxErrors = state.errors.fx;
    var fxErrMap = UI.errorsByRow(fxErrors);
    var fxHtml = '<div class="hf-row" style="gap:12px">';
    Object.keys(state.fx).forEach(function (cur) {
      var hasErr = fxErrMap[-1] && fxErrMap[-1][cur];
      fxHtml += '<div style="background:var(--bg-elev);border:1px solid ' + (hasErr ? UI.STATUS_COLORS.red : "var(--border)") + ';border-radius:6px;padding:10px 14px">' +
        '<div style="color:var(--text-muted);font-size:11px;margin-bottom:4px">1 ' + cur + '</div>' +
        '<div style="font-size:13px"><input type="number" step="0.01" class="hf-input fx-input' + (hasErr ? ' hf-input-error' : '') + '" data-cur="' + cur + '" value="' + state.fx[cur] + '"></div>' +
        '</div>';
    });
    fxHtml += '</div>';
    html += fxHtml;

    $("page-data").innerHTML = html;

    // 绑定
    UI.setTableRows("tbl-household", state.household);
    UI.bindEditableTable("tbl-household",
      function (copy) { App.setHousehold(copy); },
      function () {}, // 无删除按钮
      function () {}  // 无添加按钮
    );
    UI.setTableRows("tbl-cashflow", state.cashflow);
    UI.bindEditableTable("tbl-cashflow",
      function (copy) { App.setCashflow(copy); },
      function () {},
      function () {}
    );

    // FX 输入
    document.querySelectorAll(".fx-input").forEach(function (el) {
      el.addEventListener("change", function () {
        var cur = el.dataset.cur;
        var val = parseFloat(el.value);
        var copy = JSON.parse(JSON.stringify(App.current.fx));
        copy[cur] = val;
        App.setFx(copy);
      });
    });

    // 重置按钮
    var resetBtn = $("btn-reset-demo");
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        if (confirm("确认重置为 Demo 数据？当前所有输入将丢失。")) {
          App.resetToDemo();
          renderDataEntry();
        }
      });
    }
  }

  // ============================================================
  // 2. Balance Sheet —— 资产负债表
  // ============================================================

  function renderBalance() {
    var state = App.current;
    if (_guardNoData(state, "page-balance")) return;
    var m = state.metrics;

    var html = '<h1>资产负债表</h1><p class="sub">总资产 HK$' + Math.round(m.A).toLocaleString() + '，总负债 HK$' + Math.round(m.L).toLocaleString() + '，净值 HK$' + Math.round(m.E).toLocaleString() + '</p>';

    // 分类汇总
    var catOrder = ["cash", "investment", "property", "other"];
    var catNames = { cash: "现金及等价", investment: "投资", property: "房产", other: "其他资产" };
    var summaryHtml = '<div class="hf-row">';
    catOrder.forEach(function (c) {
      var v = m.catTotals[c] || 0;
      summaryHtml += '<div class="hf-metric-card">' +
        '<div class="hf-metric-label">' + catNames[c] + '</div>' +
        '<div class="hf-metric-value">' + UI.hkdShort(v) + '</div>' +
        '<div class="hf-metric-hint">' + (m.E > 0 ? (v / m.E * 100).toFixed(1) + "% of 净值" : "—") + '</div>' +
        '</div>';
    });
    summaryHtml += '</div>';
    html += summaryHtml;

    // 详细列表
    var assets = state.household.filter(function (r) { return r.type === "asset"; });
    var liabs = state.household.filter(function (r) { return r.type === "liability"; });

    html += '<hr class="hf-divider">' + UI.sectionTitle("资产明细", "HK$ " + Math.round(m.A).toLocaleString());
    html += _detailTable(assets, false);
    html += '<hr class="hf-divider">' + UI.sectionTitle("负债明细", "HK$ " + Math.round(m.L).toLocaleString());
    html += _detailTable(liabs, true);

    $("page-balance").innerHTML = html;
  }

  function _detailTable(rows, isLiability) {
    // 用 Engine.applyFx 确保 hkd 列最新
    var applied = Engine.applyFx(App.current.household, App.current.cashflow, App.current.fx).household;
    var filtered = applied.filter(function (r) { return isLiability ? r.type === "liability" : r.type === "asset"; });

    var html = '<div style="background:var(--panel);border:1px solid var(--border);border-radius:8px;overflow:hidden">' +
      '<table class="hf-editable"><thead><tr>' +
      '<th>名称</th><th>类别</th><th>原值</th><th>币种</th><th>HKD 折算</th><th>流动性</th><th>备注</th>' +
      '</tr></thead><tbody>';
    filtered.forEach(function (r) {
      var catName = { cash: "现金", investment: "投资", property: "房产", other: "其他", mortgage: "按揭", consumer: "消费贷" }[r.category] || r.category;
      var liqName = { high: "高", medium: "中", low: "低" }[r.liquidity] || "—";
      html += '<tr>' +
        '<td>' + r.name + '</td>' +
        '<td>' + catName + '</td>' +
        '<td>' + Math.round(r.amount).toLocaleString() + '</td>' +
        '<td>' + r.currency + '</td>' +
        '<td><b>' + UI.hkd(r.hkd) + '</b></td>' +
        '<td>' + liqName + '</td>' +
        '<td class="hf-muted">' + (r.note || "") + '</td>' +
        '</tr>';
    });
    html += '</tbody></table></div>';
    return html;
  }

  // ============================================================
  // 3. Cash Flow —— 现金流
  // ============================================================

  function renderCashflow() {
    var state = App.current;
    if (_guardNoData(state, "page-cashflow")) return;
    var m = state.metrics;
    var inc = m.INC;
    var outAll = m.EXP_all;
    var cf = m.CF;

    var html = '<h1>现金流</h1><p class="sub">月收入 HK$' + Math.round(inc).toLocaleString() +
      '，月支出 HK$' + Math.round(outAll).toLocaleString() +
      '，月结余 HK$' + Math.round(cf).toLocaleString() + '</p>';

    html += '<div class="hf-row">' +
      UI.metricCard("月收入 INC", UI.hkdShort(inc), "共 " + m.incomeSources + " 条来源", "good") +
      UI.metricCard("必要支出 EXP_ess", UI.hkdShort(m.EXP_ess), "应急金分母", "neutral") +
      UI.metricCard("债务供款 DS", UI.hkdShort(m.DS), "DSTI 分子", "warn") +
      UI.metricCard("月结余 CF", UI.hkdShort(cf), cf >= 0 ? "正向储蓄" : "负向消耗", cf >= 0 ? "good" : "bad") +
      '</div>';

    // 图表
    html += '<hr class="hf-divider"><div class="hf-chart" style="margin-bottom:16px"><div id="chart-cf"></div></div>';

    // 明细表
    var applied = Engine.applyFx(state.household, state.cashflow, state.fx).cashflow;
    html += '<div style="background:var(--panel);border:1px solid var(--border);border-radius:8px;overflow:hidden">' +
      '<table class="hf-editable"><thead><tr>' +
      '<th>名称</th><th>方向</th><th>月金额</th><th>币种</th><th>HKD</th><th>必要</th><th>债务供款</th><th>备注</th>' +
      '</tr></thead><tbody>';
    applied.forEach(function (r) {
      var dirLabel = r.direction === "in" ? '<span style="color:' + UI.STATUS_COLORS.green + '">收入</span>' : '<span style="color:' + UI.STATUS_COLORS.red + '">支出</span>';
      html += '<tr>' +
        '<td>' + r.name + '</td><td>' + dirLabel + '</td>' +
        '<td>' + Math.round(r.monthly_amount).toLocaleString() + '</td><td>' + r.currency + '</td>' +
        '<td><b>' + UI.hkd(r.hkd) + '</b></td>' +
        '<td>' + (r.essential ? "是" : "") + '</td>' +
        '<td>' + (r.debt_service ? "是" : "") + '</td>' +
        '<td class="hf-muted">' + (r.note || "") + '</td></tr>';
    });
    html += '</tbody></table></div>';

    $("page-cashflow").innerHTML = html;
    Charts.cfBar("chart-cf", applied);
  }

  // ============================================================
  // 4. Stress Test —— 压力测试
  // ============================================================

  function renderStress() {
    var state = App.current;
    if (_guardNoData(state, "page-stress")) return;
    var m = state.metrics;
    var lim = state.limits;

    var html = '<h1>压力测试</h1><p class="sub">选择情景，对比基准 vs 压力后的各项指标。</p>';

    // 情景选择 —— 预置 + 自定义
    html += '<div class="hf-toolbar">' +
      '<label>压力情景: </label>' +
      '<select id="sc-select">' +
      Engine.SCENARIOS.map(function (s) {
        return '<option value="' + s.id + '"' + (s.defaultSelected ? " selected" : "") + '>' + s.name + '</option>';
      }).join("") +
      '<option value="custom">⚙ 自定义情景</option>' +
      '</select>' +
      '</div>';

    // 自定义滑块面板（默认隐藏，选中 custom 时显示）
    html += '<div id="custom-sliders" style="display:none">' +
      UI.sectionTitle("自定义冲击系数", "拖动滑块实时重算") +
      '<div class="hf-slider-grid">' +
      _sliderHtml("slider-income_mult",   "收入乘数",      "income_mult",        0,    1,   0.05, 1.00, "收入跌至原价的 × 倍（0 = 完全失业）") +
      _sliderHtml("slider-essential_exp", "必要支出乘数",  "essential_exp_mult", 1.0,  2.0, 0.05, 1.00, "生活费上涨系数") +
      _sliderHtml("slider-invest",        "投资资产乘数",  "invest_mult",        0.5,  1.5, 0.05, 1.00, "投资市值涨跌幅") +
      _sliderHtml("slider-property",      "房产乘数",      "property_mult",      0.5,  1.5, 0.05, 1.00, "房产估值涨跌幅") +
      _sliderHtml("slider-ds",            "债务供款乘数",  "debt_service_mult",  0.5,  2.0, 0.05, 1.00, "利率变动影响的供款乘数") +
      _sliderHtml("slider-liab",          "负债乘数",      "liability_mult",     0.5,  1.5, 0.05, 1.00, "负债本金变动（如再融资）") +
      '</div></div>';

    html += '<div id="stress-content">';
    // 初始用 defaultSelected 情景
    var defSc = Engine.SCENARIOS.find(function (s) { return s.defaultSelected; }) || Engine.SCENARIOS[8];
    html += _renderStressContent(state, m, lim, defSc);
    html += '</div>';

    $("page-stress").innerHTML = html;

    // 绑定 selector
    var sel = $("sc-select");
    var sliderPanel = $("custom-sliders");

    function _syncSlidersToScenario(sc) {
      ["income_mult", "essential_exp_mult", "invest_mult", "property_mult", "debt_service_mult", "liability_mult"].forEach(function (key) {
        var input = document.getElementById("slider-" + key);
        if (input) {
          input.value = sc[key] != null ? sc[key] : 1.0;
          var label = document.getElementById("slider-" + key + "-val");
          if (label) label.textContent = (sc[key] != null ? sc[key] : 1.0).toFixed(2) + "×";
        }
      });
    }

    function _readSliders() {
      var result = {};
      ["income_mult", "essential_exp_mult", "invest_mult", "property_mult", "debt_service_mult", "liability_mult"].forEach(function (key) {
        var input = document.getElementById("slider-" + key);
        result[key] = input ? parseFloat(input.value) : 1.0;
      });
      return result;
    }

    function _currentScenario() {
      var v = sel.value;
      if (v === "custom") {
        var custom = _readSliders();
        custom.id = "custom";
        custom.name = "自定义情景";
        return custom;
      }
      return Engine.SCENARIOS.find(function (s) { return s.id === v; }) || Engine.SCENARIOS[0];
    }

    function _refreshStress() {
      var sc = _currentScenario();
      $("stress-content").innerHTML = _renderStressContent(App.current, App.current.metrics, App.current.limits, sc);
    }

    if (sel) {
      sel.addEventListener("change", function () {
        if (sel.value === "custom") {
          sliderPanel.style.display = "";
          // 用 defaultSelected 情景作为起点让用户微调
          var defaultSc = Engine.SCENARIOS.find(function (s) { return s.defaultSelected; }) || Engine.SCENARIOS[8];
          _syncSlidersToScenario(defaultSc);
        } else {
          sliderPanel.style.display = "none";
        }
        _refreshStress();
      });
    }

    // 滑块变化触发重算
    document.querySelectorAll("[data-slider]").forEach(function (el) {
      el.addEventListener("input", function () {
        var key = el.dataset.slider;
        var label = document.getElementById("slider-" + key + "-val");
        if (label) label.textContent = parseFloat(el.value).toFixed(2) + "×";
      });
      el.addEventListener("change", function () {
        _refreshStress();
      });
    });
  }

  function _sliderHtml(id, label, key, min, max, step, defaultVal, hint) {
    return '<div class="hf-slider-item">' +
      '<div class="hf-slider-head">' +
        '<label for="' + id + '">' + label + '</label>' +
        '<span class="hf-slider-val" id="' + id + '-val">' + defaultVal.toFixed(2) + '×</span>' +
      '</div>' +
      '<input type="range" id="' + id + '" data-slider="' + key + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + defaultVal + '">' +
      '<div class="hf-slider-foot"><span>' + min + '×</span><span>' + max + '×</span></div>' +
      (hint ? '<div class="hf-muted" style="font-size:11px;margin-top:2px">' + hint + '</div>' : '') +
      '</div>';
  }

  function _renderStressContent(state, m, lim, scenario) {
    var applied = Engine.applyFx(state.household, state.cashflow, state.fx);
    var stressMetrics = Engine.computeMetrics(applied.household, applied.cashflow, scenario);
    var stressLimits = Engine.checkAllLimits(stressMetrics);
    var cmp = Engine.compareScenarios(m, stressMetrics, lim, stressLimits);

    var sb = UI.statusColor(lim.overall);
    var ss = UI.statusColor(stressLimits.overall);

    var html = '';

    // 顶部灯号对比
    html += '<div class="hf-split hf-split-2-1" style="margin-bottom:16px">' +
      '<div class="hf-big-light">' +
        '<div class="hf-big-light-dot" style="background:' + sb + ';color:' + sb + '"></div>' +
        '<div class="hf-big-light-body">' +
          '<h2>基准: ' + UI.statusLabel(lim.overall) + '</h2>' +
          '<p>' + scenario.name + ' 下综合灯: <span style="color:' + ss + ';font-weight:600">' + UI.statusLabel(stressLimits.overall) + '</span>' +
          (cmp.overall_changed ? "（变化）" : "（不变）") + '</p>' +
        '</div>' +
      '</div>' +
      '<div class="hf-chart"><div id="stress-cmp-chart"></div></div>' +
    '</div>';

    // 对比表
    html += '<div class="hf-card" style="margin-bottom:16px">' +
      UI.sectionTitle("指标变化对比", "基准 → 压力") +
      '<table class="hf-compare-table"><thead><tr>' +
      '<th>指标</th><th>单位</th><th>基准</th><th>压力后</th><th>变化</th>' +
      '</tr></thead><tbody>' +
      cmp.comparison.map(function (c) {
        var diffClass = c.diff != null ? (c.diff > 0 ? "hf-diff-pos" : c.diff < 0 ? "hf-diff-neg" : "") : "";
        return '<tr><td>' + c.name + '</td><td>' + c.unit + '</td><td>' + c.baseline_display + '</td><td>' + c.stress_display + '</td><td class="' + diffClass + '">' + c.diff_display + '</td></tr>';
      }).join("") +
      '</tbody></table></div>';

    // 击穿清单
    html += '<div class="hf-card" style="margin-bottom:16px">' +
      UI.sectionTitle("击穿清单", "stress 灯变为红且 base 非红") +
      (cmp.breaches.length === 0 ?
        '<div class="hf-muted" style="padding:16px;text-align:center">本次情景无新增击穿项</div>' :
        '<ul class="hf-breach-list">' + cmp.breaches.map(function (b) {
          return '<li><span><b>' + b.name + '</b></span>' +
            '<span class="hf-breach-from">' + UI.statusLabel(b.baseline_status) + '</span>' +
            '<span class="hf-breach-arrow">→</span>' +
            '<span class="hf-breach-to">' + UI.statusLabel(b.stress_status) + '</span>' +
            '<span style="flex:1"></span><span class="hf-muted">' + b.reason + '</span></li>';
        }).join("") + '</ul>') +
    '</div>';

    // 失业辅助
    var u = stressMetrics.unemployment;
    html += '<div class="hf-card">' +
      UI.sectionTitle("失业辅助数据", "收入中断视角") +
      '<div class="hf-row">' +
        UI.metricCard("3个月必要支出", UI.hkdShort(u.need3), "EXP_ess × 3", "neutral") +
        UI.metricCard("6个月必要支出", UI.hkdShort(u.need6), "EXP_ess × 6", "neutral") +
        UI.metricCard("3个月缺口", u.gap3 === 0 ? "无缺口" : UI.hkdShort(u.gap3), "max(0, 3×EXP − A_high)", u.gap3 > 0 ? "warn" : "good") +
        UI.metricCard("6个月缺口", u.gap6 === 0 ? "无缺口" : UI.hkdShort(u.gap6), "max(0, 6×EXP − A_high)", u.gap6 > 0 ? "warn" : "good") +
      '</div></div>';

    // 渲染图表（需要 DOM 在）
    setTimeout(function () {
      if (window.Plotly) Charts.stressCompareBar("stress-cmp-chart", cmp);
    }, 0);

    return html;
  }

  // ============================================================
  // 5. Limits —— 限额与假设
  // ============================================================

  function renderLimits() {
    var state = App.current;
    if (_guardNoData(state, "page-limits")) return;
    var lim = state.limits;
    var m = state.metrics;

    var html = '<h1>限额与假设</h1><p class="sub">7 条核心风险限额的当前状态与定义。</p>';

    html += '<div class="hf-limit-list">';
    lim.limits.forEach(function (l) {
      var color = UI.statusColor(l.status);
      html += '<div class="hf-limit-row">' +
        '<div style="display:flex;align-items:center;gap:8px">' +
          '<span class="hf-dot" style="background:' + color + '"></span>' +
          '<span class="hf-limit-name">' + l.name + '</span>' +
        '</div>' +
        '<div style="font-size:13px">' +
          '<b>' + (l.display || "N/A") + '</b>' +
        '</div>' +
        '<div class="hf-limit-yellow">黄: ' + l.yellow + '</div>' +
        '<div class="hf-limit-red">红: ' + l.red + '</div>' +
        '<div class="hf-limit-cur">' + l.reason + '</div>' +
        '</div>';
    });
    html += '</div>';

    html += '<hr class="hf-divider">' +
      '<div class="hf-muted" style="padding:16px">' +
      '<b style="color:var(--text-primary)">综合规则:</b> 综合灯取 7 条限额中最差灯（green=0, yellow=1, red=2）。' +
      '当前综合灯: <span style="color:' + UI.statusColor(lim.overall) + ';font-weight:600">' + UI.statusLabel(lim.overall) + '</span>。' +
      '<br><b style="color:var(--text-primary)">假设:</b> 所有金额以 HKD 折算；"高流动性" 指现金类资产，不包含可变现但有价格波动的投资。' +
      '</div>';

    $("page-limits").innerHTML = html;
  }

  // ============================================================
  // 路由
  // ============================================================

  var PAGES = {
    dashboard: renderDashboard,
    data: renderDataEntry,
    balance: renderBalance,
    cashflow: renderCashflow,
    stress: renderStress,
    limits: renderLimits,
  };

  function navigate(hash) {
    hash = (hash || "dashboard").replace(/^#/, "");
    if (!PAGES[hash]) hash = "dashboard";

    // nav active
    document.querySelectorAll(".hf-nav a").forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("href") === "#" + hash);
    });
    // hide all, show current
    document.querySelectorAll("[data-page]").forEach(function (el) {
      el.style.display = el.dataset.page === hash ? "" : "none";
    });
    // render
    if (PAGES[hash]) PAGES[hash]();
  }

  function init() {
    // 订阅 state 变化 —— 如果停留在当前页则重渲染
    App.onChange(function () {
      var hash = (location.hash || "#dashboard").replace(/^#/, "");
      if (PAGES[hash]) PAGES[hash]();
    });

    // 初始导航
    window.addEventListener("hashchange", function () { navigate(location.hash); });
    navigate(location.hash || "#dashboard");
  }

  root.Pages = {
    init: init,
    navigate: navigate,
    renderDashboard: renderDashboard,
    renderDataEntry: renderDataEntry,
    renderBalance: renderBalance,
    renderCashflow: renderCashflow,
    renderStress: renderStress,
    renderLimits: renderLimits,
  };

})(typeof window !== "undefined" ? window : globalThis);
