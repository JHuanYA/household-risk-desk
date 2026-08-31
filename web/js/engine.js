/**
 * 计算引擎 —— 完整移植自 Python 版 metrics.py / limits.py / scenarios.py
 * 与 streamlit 版数值逐行验证一致
 *
 * 命名空间: window.Engine
 */
(function (root) {
  "use strict";

  // ============================================================
  // 配置常量
  // ============================================================

  const DEFAULT_FX = {
    HKD: 1,
    USD: 7.8,
    CNY: 1.08,
  };

  const DEFAULT_LIMITS = {
    lim_target_months: 6,
    lim_yellow_below: 6,
    lim_red_below: 3,
    lev_yellow_above: 0.4,
    lev_red_above: 0.6,
    dsti_yellow_above: 0.4,
    dsti_red_above: 0.5,
    invest_yellow_above: 0.6,
    invest_red_above: 0.8,
    concentration_yellow_above: 0.7,
    concentration_red_above: 0.9,
  };

  // ============================================================
  // 汇率折算
  // ============================================================

  function toHkd(amount, currency, fx) {
    fx = fx || DEFAULT_FX;
    const rate = fx[currency];
    if (rate == null) {
      throw new Error("缺少汇率: " + currency);
    }
    return amount * rate;
  }

  function applyFx(householdRows, cashflowRows, fx) {
    return {
      household: householdRows.map(function (r) {
        var out = {};
        for (var k in r) out[k] = r[k];
        out.hkd = toHkd(r.amount, r.currency, fx);
        return out;
      }),
      cashflow: cashflowRows.map(function (r) {
        var out = {};
        for (var k in r) out[k] = r[k];
        out.hkd = toHkd(r.monthly_amount, r.currency, fx);
        return out;
      }),
    };
  }

  // ============================================================
  // 核心指标计算 —— 对齐 src/metrics.py
  // ============================================================

  function computeMetrics(householdRows, cashflowRows, shock) {
    shock = shock || {};
    const incomeMult = shock.income_mult == null ? 1 : shock.income_mult;
    const essMult = shock.essential_exp_mult == null ? 1 : shock.essential_exp_mult;
    const investMult = shock.invest_mult == null ? 1 : shock.invest_mult;
    const propertyMult = shock.property_mult == null ? 1 : shock.property_mult;
    const dsMult = shock.debt_service_mult == null ? 1 : shock.debt_service_mult;
    const liabMult = shock.liability_mult == null ? 1 : shock.liability_mult;

    const assets = householdRows.filter(function (r) { return r.type === "asset"; });
    const liabs = householdRows.filter(function (r) { return r.type === "liability"; });

    function assetHkd(r) {
      if (r.category === "investment") return r.hkd * investMult;
      if (r.category === "property") return r.hkd * propertyMult;
      return r.hkd;
    }

    const A = assets.reduce(function (s, r) { return s + assetHkd(r); }, 0);
    const L = liabs.reduce(function (s, r) { return s + r.hkd * liabMult; }, 0);
    const E = A - L;

    const A_high = assets
      .filter(function (r) { return r.liquidity === "high"; })
      .reduce(function (s, r) { return s + r.hkd; }, 0);
    const A_invest = assets
      .filter(function (r) { return r.category === "investment"; })
      .reduce(function (s, r) { return s + assetHkd(r); }, 0);
    const A_property = assets
      .filter(function (r) { return r.category === "property"; })
      .reduce(function (s, r) { return s + assetHkd(r); }, 0);
    const A_cash = assets
      .filter(function (r) { return r.category === "cash"; })
      .reduce(function (s, r) { return s + r.hkd; }, 0);
    const A_other = assets
      .filter(function (r) { return r.category === "other"; })
      .reduce(function (s, r) { return s + r.hkd; }, 0);

    const catTotals = {};
    assets.forEach(function (r) {
      const v = assetHkd(r);
      catTotals[r.category] = (catTotals[r.category] || 0) + v;
    });
    let maxCat = null;
    let maxCatAmt = 0;
    Object.keys(catTotals).forEach(function (k) {
      if (catTotals[k] > maxCatAmt) { maxCatAmt = catTotals[k]; maxCat = k; }
    });

    const INC = cashflowRows
      .filter(function (r) { return r.direction === "in"; })
      .reduce(function (s, r) { return s + r.hkd * incomeMult; }, 0);

    const EXP_ess = cashflowRows
      .filter(function (r) { return r.direction === "out" && r.essential === 1; })
      .reduce(function (s, r) {
        const m = r.debt_service === 1 ? dsMult * essMult : essMult;
        return s + r.hkd * m;
      }, 0);

    const DS = cashflowRows
      .filter(function (r) { return r.direction === "out" && r.debt_service === 1; })
      .reduce(function (s, r) { return s + r.hkd * dsMult; }, 0);

    const EXP_all = cashflowRows
      .filter(function (r) { return r.direction === "out"; })
      .reduce(function (s, r) {
        if (r.debt_service === 1) return s + r.hkd * dsMult * (r.essential === 1 ? essMult : 1);
        if (r.essential === 1) return s + r.hkd * essMult;
        return s + r.hkd;
      }, 0);

    // 收入来源数
    const ranks = {};
    cashflowRows.forEach(function (r) {
      if (r.direction === "in" && r.hkd * incomeMult > 0 && r.source_rank != null && r.source_rank !== "") {
        ranks[r.source_rank] = true;
      }
    });
    const incomeSources = Object.keys(ranks).length;

    const limAvailable = EXP_ess > 0;
    const LIM = limAvailable ? A_high / EXP_ess : null;
    const LID = LIM != null ? LIM * 30 : null;
    const GAP = limAvailable ? Math.max(0, 6 * EXP_ess - A_high) : null;
    const LEV = A > 0 ? L / A : Infinity;
    const DSTI = INC > 0 ? DS / INC : DS > 0 ? Infinity : null;
    const investRatio = E > 0 ? A_invest / E : null;
    const propertyRatio = E > 0 ? A_property / E : null;
    const maxCatRatio = E > 0 ? maxCatAmt / E : null;

    return {
      A: A, L: L, E: E,
      A_high: A_high, A_cash: A_cash, A_invest: A_invest,
      A_property: A_property, A_other: A_other,
      maxCat: maxCat, maxCatAmt: maxCatAmt,
      catTotals: catTotals,
      INC: INC, EXP_ess: EXP_ess, EXP_all: EXP_all,
      DS: DS, CF: INC - EXP_all,
      incomeSources: incomeSources,
      LIM: LIM, LID: LID, GAP: GAP,
      LEV: LEV, DSTI: DSTI,
      investRatio: investRatio,
      propertyRatio: propertyRatio,
      maxCatRatio: maxCatRatio,
      limAvailable: limAvailable,
      // 失业辅助（任何情景都输出，方便前端使用）
      unemployment: {
        need3: EXP_ess * 3,
        need6: EXP_ess * 6,
        gap3: Math.max(0, EXP_ess * 3 - A_high),
        gap6: Math.max(0, EXP_ess * 6 - A_high),
        monthsCovered: LIM,
      },
    };
  }

  // ============================================================
  // 限额判断 —— 对齐 src/limits.py
  // ============================================================

  const RANK = { green: 0, yellow: 1, red: 2 };
  const CAT_NAMES = { cash: "现金及等价", investment: "投资", property: "房产", other: "其他资产" };

  function worst(a, b) {
    return RANK[a] >= RANK[b] ? a : b;
  }

  function checkAllLimits(metrics, config) {
    config = config || DEFAULT_LIMITS;
    const results = [];

    // 1. LIM 流动性月数
    (function () {
      const lim = metrics.LIM;
      const avail = metrics.limAvailable;
      if (!avail || lim == null) {
        results.push({ id: "LIM", name: "流动性月数", value: null, display: "不可用", status: "red",
          yellow: "< " + config.lim_target_months, red: "< " + config.lim_red_below,
          reason: "必要支出未录入，流动性指标不可用" });
        return;
      }
      let status;
      if (lim < config.lim_red_below) status = "red";
      else if (lim < config.lim_yellow_below) status = "yellow";
      else status = "green";
      results.push({ id: "LIM", name: "流动性月数", value: lim, display: lim.toFixed(2) + " 个月", status: status,
        yellow: "< " + config.lim_yellow_below, red: "< " + config.lim_red_below,
        reason: "高流动性资产可覆盖 " + lim.toFixed(2) + " 个月必要支出，目标 " + config.lim_target_months + " 个月" });
    })();

    // 2. LEV 杠杆
    (function () {
      const lev = metrics.LEV;
      if (!isFinite(lev)) {
        results.push({ id: "LEV", name: "杠杆 L/A", value: null, display: "无穷大", status: "red",
          yellow: "> " + (config.lev_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.lev_red_above * 100).toFixed(0) + "%",
          reason: "资产为零，杠杆无穷大" });
        return;
      }
      let status;
      if (lev > config.lev_red_above) status = "red";
      else if (lev > config.lev_yellow_above) status = "yellow";
      else status = "green";
      results.push({ id: "LEV", name: "杠杆 L/A", value: lev, display: (lev * 100).toFixed(2) + "%", status: status,
        yellow: "> " + (config.lev_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.lev_red_above * 100).toFixed(0) + "%",
        reason: (status !== "green" ? "负债占总资产 " : "负债占总资产 ") + (lev * 100).toFixed(2) + "%" });
    })();

    // 3. E 净值
    (function () {
      const e = metrics.E || 0;
      const status = e < 0 ? "red" : "green";
      results.push({ id: "E", name: "净值", value: e, display: "HK$" + Math.round(e).toLocaleString(), status: status,
        yellow: "—", red: "< 0",
        reason: e < 0 ? "净资产为负，已触发偿付危机定义" : "净资产为正" });
    })();

    // 4. DSTI 偿债比率
    (function () {
      const dsti = metrics.DSTI;
      if (dsti == null) {
        results.push({ id: "DSTI", name: "偿债比率 DSTI", value: null, display: "不适用", status: "green",
          yellow: "> " + (config.dsti_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.dsti_red_above * 100).toFixed(0) + "%",
          reason: "收入和债务供款均为零" });
        return;
      }
      if (!isFinite(dsti)) {
        results.push({ id: "DSTI", name: "偿债比率 DSTI", value: null, display: "不适用", status: "red",
          yellow: "> " + (config.dsti_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.dsti_red_above * 100).toFixed(0) + "%",
          reason: "收入为零但仍有债务供款" });
        return;
      }
      let status;
      if (dsti > config.dsti_red_above) status = "red";
      else if (dsti > config.dsti_yellow_above) status = "yellow";
      else status = "green";
      results.push({ id: "DSTI", name: "偿债比率 DSTI", value: dsti, display: (dsti * 100).toFixed(2) + "%", status: status,
        yellow: "> " + (config.dsti_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.dsti_red_above * 100).toFixed(0) + "%",
        reason: (status !== "green" ? "月供款占收入 " : "月供款占收入 ") + (dsti * 100).toFixed(2) + "%" });
    })();

    // 5. INVEST 投资/净值
    (function () {
      const e = metrics.E || 0;
      if (e <= 0) {
        results.push({ id: "INVEST", name: "投资 / 净值", value: null, display: "不适用", status: "red",
          yellow: "> " + (config.invest_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.invest_red_above * 100).toFixed(0) + "%",
          reason: "净值不为正，集中度不输出百分比" });
        return;
      }
      const ir = metrics.investRatio;
      if (ir == null) {
        results.push({ id: "INVEST", name: "投资 / 净值", value: null, display: "N/A", status: "green",
          yellow: "> " + (config.invest_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.invest_red_above * 100).toFixed(0) + "%",
          reason: "无投资类资产" });
        return;
      }
      let status;
      if (ir > config.invest_red_above) status = "red";
      else if (ir > config.invest_yellow_above) status = "yellow";
      else status = "green";
      results.push({ id: "INVEST", name: "投资 / 净值", value: ir, display: (ir * 100).toFixed(2) + "%", status: status,
        yellow: "> " + (config.invest_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.invest_red_above * 100).toFixed(0) + "%",
        reason: "投资类资产占净值 " + (ir * 100).toFixed(2) + "%" });
    })();

    // 6. CONC 单一类别集中度
    (function () {
      const e = metrics.E || 0;
      if (e <= 0) {
        results.push({ id: "CONC", name: "单一类别 / 净值", value: null, display: "不适用", status: "red",
          yellow: "> " + (config.concentration_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.concentration_red_above * 100).toFixed(0) + "%",
          reason: "净值不为正，集中度不输出百分比" });
        return;
      }
      const mr = metrics.maxCatRatio;
      const mc = metrics.maxCat;
      if (mr == null) {
        results.push({ id: "CONC", name: "单一类别 / 净值", value: null, display: "N/A", status: "green",
          yellow: "> " + (config.concentration_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.concentration_red_above * 100).toFixed(0) + "%",
          reason: "无明确最大类别" });
        return;
      }
      let status;
      if (mr > config.concentration_red_above) status = "red";
      else if (mr > config.concentration_yellow_above) status = "yellow";
      else status = "green";
      results.push({ id: "CONC", name: "单一类别 / 净值", value: mr, display: (mr * 100).toFixed(2) + "%", status: status,
        yellow: "> " + (config.concentration_yellow_above * 100).toFixed(0) + "%", red: "> " + (config.concentration_red_above * 100).toFixed(0) + "%",
        reason: "类别 " + (CAT_NAMES[mc] || mc) + " 占净值 " + (mr * 100).toFixed(2) + "%" });
    })();

    // 7. INCOME 收入单一性
    (function () {
      const sources = metrics.incomeSources || 0;
      const lim = metrics.LIM;
      const avail = metrics.limAvailable;
      let status;
      if (sources <= 1 && avail && lim != null) {
        if (lim < 3) status = "red";
        else if (lim < config.lim_target_months) status = "yellow";
        else status = "green";
      } else {
        status = "green";
      }
      results.push({ id: "INCOME", name: "收入单一性", value: sources, display: sources + " 条", status: status,
        yellow: "来源≤1 且 LIM<6", red: "来源≤1 且 LIM<3",
        reason: "收入来源 " + sources + " 条" });
    })();

    // 综合灯
    let overall = "green";
    results.forEach(function (x) { overall = worst(overall, x.status); });
    const alerts = results.filter(function (x) { return x.status !== "green"; });

    return { limits: results, alerts: alerts, overall: overall };
  }

  // ============================================================
  // compare_scenarios —— 对齐 src/scenarios.py
  // ============================================================

  function compareScenarios(baselineMetrics, stressMetrics, baselineLimits, stressLimits) {
    const compareKeys = [
      ["E", "净值", "HKD"],
      ["A", "资产", "HKD"],
      ["L", "负债", "HKD"],
      ["A_high", "高流动性资产", "HKD"],
      ["LIM", "流动性月数", "月"],
      ["GAP", "应急金缺口", "HKD"],
      ["LEV", "杠杆", "%"],
      ["DSTI", "DSTI", "%"],
    ];

    function fmtHKD(v) { return v == null ? "N/A" : "HK$" + Math.round(v).toLocaleString(); }
    function fmtPct(v) { return v == null ? "N/A" : !isFinite(v) ? "∞" : (v * 100).toFixed(2) + "%"; }
    function fmtMonth(v) { return v == null ? "N/A" : !isFinite(v) ? "∞" : v.toFixed(2); }
    function fmt(key, v) {
      if (v == null) return "N/A";
      if (key === "%") return fmtPct(v);
      if (key === "HKD") return fmtHKD(v);
      return fmtMonth(v);
    }

    const comparison = [];
    compareKeys.forEach(function (kv) {
      const key = kv[0], name = kv[1], unit = kv[2];
      const base = baselineMetrics[key];
      const stress = stressMetrics[key];
      let diff = null;
      if (base != null && stress != null && isFinite(base) && isFinite(stress)) {
        diff = stress - base;
      }
      let diffDisp = "N/A";
      if (diff != null) {
        if (unit === "HKD") diffDisp = (diff >= 0 ? "+" : "") + fmtHKD(diff);
        else if (unit === "%") diffDisp = (diff >= 0 ? "+" : "") + (diff * 100).toFixed(2) + "%";
        else diffDisp = (diff >= 0 ? "+" : "") + diff.toFixed(2);
      }
      comparison.push({
        key: key, name: name, unit: unit,
        baseline: base, baseline_display: fmt(unit, base),
        stress: stress, stress_display: fmt(unit, stress),
        diff: diff, diff_display: diffDisp,
      });
    });

    const baseLimits = baselineLimits.limits || [];
    const stressLimitDict = {};
    (stressLimits.limits || []).forEach(function (l) { stressLimitDict[l.id] = l; });

    const breaches = [];
    baseLimits.forEach(function (bl) {
      const sl = stressLimitDict[bl.id];
      if (sl && sl.status === "red" && bl.status !== "red") {
        breaches.push({
          id: bl.id, name: bl.name,
          baseline_status: bl.status, stress_status: sl.status,
          reason: sl.reason || "",
        });
      }
    });

    return {
      comparison: comparison,
      breaches: breaches,
      overall_baseline: baselineLimits.overall,
      overall_stress: stressLimits.overall,
      overall_changed: baselineLimits.overall !== stressLimits.overall,
    };
  }

  // ============================================================
  // 预置情景
  // ============================================================

  const SCENARIOS = [
    { id: "base",           name: "基准",                         income_mult: 1,  essential_exp_mult: 1, invest_mult: 1, property_mult: 1,  debt_service_mult: 1,   liability_mult: 1 },
    { id: "jobloss3",       name: "失业 3 个月视角",              income_mult: 0,  essential_exp_mult: 1, invest_mult: 1, property_mult: 1,  debt_service_mult: 1,   liability_mult: 1 },
    { id: "jobloss6",       name: "失业 6 个月视角",              income_mult: 0,  essential_exp_mult: 1, invest_mult: 1, property_mult: 1,  debt_service_mult: 1,   liability_mult: 1 },
    { id: "invest20",       name: "投资下跌 20%",                 income_mult: 1,  essential_exp_mult: 1, invest_mult: 0.8, property_mult: 1, debt_service_mult: 1,   liability_mult: 1 },
    { id: "invest40",       name: "投资下跌 40%",                 income_mult: 1,  essential_exp_mult: 1, invest_mult: 0.6, property_mult: 1, debt_service_mult: 1,   liability_mult: 1 },
    { id: "property15",     name: "房价下跌 15%",                 income_mult: 1,  essential_exp_mult: 1, invest_mult: 1, property_mult: 0.85, debt_service_mult: 1, liability_mult: 1 },
    { id: "property30",     name: "房价下跌 30%",                 income_mult: 1,  essential_exp_mult: 1, invest_mult: 1, property_mult: 0.70, debt_service_mult: 1, liability_mult: 1 },
    { id: "rate20",         name: "供款上升 20%",                 income_mult: 1,  essential_exp_mult: 1, invest_mult: 1, property_mult: 1,  debt_service_mult: 1.2, liability_mult: 1 },
    { id: "combo_job_invest", name: "联合：失业+投资下跌20%",     income_mult: 0,  essential_exp_mult: 1, invest_mult: 0.8, property_mult: 1, debt_service_mult: 1, liability_mult: 1, defaultSelected: true },
    { id: "combo_housing",  name: "联合：失业+房价-15%+供款+20%", income_mult: 0, essential_exp_mult: 1, invest_mult: 1, property_mult: 0.85, debt_service_mult: 1.2, liability_mult: 1 },
  ];

  // ============================================================
  // Demo 初始数据
  // ============================================================

  const DEMO_HOUSEHOLD = [
    { item_id: "CASH_HSBC",   name: "汇丰港币活期",    type: "asset",     category: "cash",       amount: 80000,  currency: "HKD", liquidity: "high",   owner: "本人", monthly_payment: null, note: "应急金主体" },
    { item_id: "CASH_USD_MM", name: "美元货币基金",    type: "asset",     category: "cash",       amount: 5000,   currency: "USD", liquidity: "high",   owner: "本人", monthly_payment: null, note: "高流动性；按汇率折港币" },
    { item_id: "INV_HK",      name: "港股及基金组合",  type: "asset",     category: "investment", amount: 350000, currency: "HKD", liquidity: "medium", owner: "本人", monthly_payment: null, note: "可变现但有价格波动" },
    { item_id: "INV_US",      name: "美股ETF",         type: "asset",     category: "investment", amount: 15000,  currency: "USD", liquidity: "medium", owner: "本人", monthly_payment: null, note: "可变现但有价格波动" },
    { item_id: "PROP_HOME",   name: "自住物业估值",    type: "asset",     category: "property",   amount: 5500000, currency: "HKD", liquidity: "low",    owner: "共同", monthly_payment: null, note: "自住房；可变现差" },
    { item_id: "OTHER_MPF",   name: "强积金估算",      type: "asset",     category: "other",      amount: 20000,  currency: "HKD", liquidity: "low",    owner: "本人", monthly_payment: null, note: "提取受限" },
    { item_id: "LIAB_MTG",    name: "住宅按揭余额",    type: "liability", category: "mortgage",   amount: 2400000, currency: "HKD", liquidity: null,     owner: "共同", monthly_payment: 18000, note: "供款以现金流表为准" },
    { item_id: "LIAB_CC",     name: "信用卡应还余额",  type: "liability", category: "consumer",  amount: 45000,  currency: "HKD", liquidity: null,     owner: "本人", monthly_payment: 3000,  note: "计划还款额见现金流" },
  ];

  const DEMO_CASHFLOW = [
    { item_id: "INC_SALARY", name: "主职月薪",      direction: "in",  monthly_amount: 48000, currency: "HKD", essential: 0, debt_service: 0, source_rank: 1,    note: "唯一收入来源" },
    { item_id: "OUT_MTG",    name: "按揭供款",      direction: "out", monthly_amount: 18000, currency: "HKD", essential: 1, debt_service: 1, source_rank: null, note: "必要支出且计入DSTI" },
    { item_id: "OUT_CC",     name: "信用卡计划还款", direction: "out", monthly_amount: 3000,  currency: "HKD", essential: 1, debt_service: 1, source_rank: null, note: "必要支出且计入DSTI" },
    { item_id: "OUT_FOOD",   name: "食杂",          direction: "out", monthly_amount: 8000,  currency: "HKD", essential: 1, debt_service: 0, source_rank: null, note: "必要生活支出" },
    { item_id: "OUT_UTIL",   name: "水电煤及网络",  direction: "out", monthly_amount: 2500,  currency: "HKD", essential: 1, debt_service: 0, source_rank: null, note: "必要生活支出" },
    { item_id: "OUT_TRANS",  name: "交通",          direction: "out", monthly_amount: 2000,  currency: "HKD", essential: 1, debt_service: 0, source_rank: null, note: "必要生活支出" },
    { item_id: "OUT_INS",    name: "保险",          direction: "out", monthly_amount: 1500,  currency: "HKD", essential: 1, debt_service: 0, source_rank: null, note: "必要支出" },
    { item_id: "OUT_DINE",   name: "外出用餐",      direction: "out", monthly_amount: 4000,  currency: "HKD", essential: 0, debt_service: 0, source_rank: null, note: "非必要" },
    { item_id: "OUT_SUB",    name: "订阅与娱乐",    direction: "out", monthly_amount: 800,   currency: "HKD", essential: 0, debt_service: 0, source_rank: null, note: "非必要" },
  ];

  // ============================================================
  // 输入校验 —— P0: 风控红线，垃圾输入不允许进入计算
  // ============================================================

  const VALID_TYPES = { asset: true, liability: true };
  const VALID_CATS_ASSET = { cash: true, investment: true, property: true, other: true };
  const VALID_CATS_LIAB  = { mortgage: true, consumer: true, other: true };
  const VALID_LIQ = { high: true, medium: true, low: true };
  const VALID_DIR = { in: true, out: true };
  const VALID_BOOL = { 0: true, 1: true };
  const VALID_CURRENCIES = { HKD: true, USD: true, CNY: true };

  /**
   * 校验 household 表
   * @returns {Array<{rowIdx, field, message}>} errors
   */
  function validateHousehold(rows, fx) {
    var errors = [];
    rows.forEach(function (r, idx) {
      var prefix = "household[" + idx + "]";
      // name — 非空
      if (!r.name || String(r.name).trim() === "") {
        errors.push({ rowIdx: idx, field: "name", message: "名称不能为空" });
      }
      // type
      if (!VALID_TYPES[r.type]) {
        errors.push({ rowIdx: idx, field: "type", message: "类型必须是 asset 或 liability，当前=" + r.type });
      }
      // category
      if (r.type === "asset" && !VALID_CATS_ASSET[r.category]) {
        errors.push({ rowIdx: idx, field: "category", message: "资产类别无效: " + r.category });
      }
      if (r.type === "liability" && !VALID_CATS_LIAB[r.category]) {
        errors.push({ rowIdx: idx, field: "category", message: "负债类别无效: " + r.category });
      }
      // amount — 必须是数字且 >= 0
      if (r.amount == null || r.amount === "" || isNaN(Number(r.amount))) {
        errors.push({ rowIdx: idx, field: "amount", message: "金额必须是数字" });
      } else if (Number(r.amount) < 0) {
        errors.push({ rowIdx: idx, field: "amount", message: "金额不能为负数 (" + r.amount + ")" });
      }
      // currency — 必须有汇率
      if (!r.currency || !fx[r.currency]) {
        errors.push({ rowIdx: idx, field: "currency", message: "币种 " + r.currency + " 无对应汇率" });
      }
      // liquidity — 如果是资产，必须是 high/medium/low
      if (r.type === "asset" && r.liquidity != null && r.liquidity !== "" && !VALID_LIQ[r.liquidity]) {
        errors.push({ rowIdx: idx, field: "liquidity", message: "流动性必须是 high/medium/low" });
      }
    });
    // 整体校验：不能所有行都是 0
    var totalAsset = rows.filter(function (r) { return r.type === "asset"; }).reduce(function (s, r) { return s + (Number(r.amount) || 0); }, 0);
    var totalLiab = rows.filter(function (r) { return r.type === "liability"; }).reduce(function (s, r) { return s + (Number(r.amount) || 0); }, 0);
    if (totalAsset === 0 && rows.some(function (r) { return r.type === "asset"; })) {
      errors.push({ rowIdx: -1, field: "_total", message: "资产总额为 0，计算出的杠杆将为 Infinity" });
    }
    return errors;
  }

  /**
   * 校验 cashflow 表
   */
  function validateCashflow(rows, fx) {
    var errors = [];
    rows.forEach(function (r, idx) {
      // name
      if (!r.name || String(r.name).trim() === "") {
        errors.push({ rowIdx: idx, field: "name", message: "名称不能为空" });
      }
      // direction
      if (!VALID_DIR[r.direction]) {
        errors.push({ rowIdx: idx, field: "direction", message: "方向必须是 in 或 out" });
      }
      // monthly_amount
      if (r.monthly_amount == null || r.monthly_amount === "" || isNaN(Number(r.monthly_amount))) {
        errors.push({ rowIdx: idx, field: "monthly_amount", message: "月金额必须是数字" });
      } else if (Number(r.monthly_amount) < 0) {
        errors.push({ rowIdx: idx, field: "monthly_amount", message: "月金额不能为负数" });
      }
      // currency
      if (!r.currency || !fx[r.currency]) {
        errors.push({ rowIdx: idx, field: "currency", message: "币种 " + r.currency + " 无对应汇率" });
      }
      // essential / debt_service 必须是 0 或 1
      if (r.essential != null && String(r.essential) !== "" && !VALID_BOOL[Number(r.essential)]) {
        errors.push({ rowIdx: idx, field: "essential", message: "essential 必须是 0 或 1" });
      }
      if (r.debt_service != null && String(r.debt_service) !== "" && !VALID_BOOL[Number(r.debt_service)]) {
        errors.push({ rowIdx: idx, field: "debt_service", message: "debt_service 必须是 0 或 1" });
      }
      // source_rank — 只有收入行才需要
      if (r.direction === "in" && r.source_rank != null && r.source_rank !== "" && Number(r.source_rank) < 0) {
        errors.push({ rowIdx: idx, field: "source_rank", message: "source_rank 不能为负数" });
      }
    });
    return errors;
  }

  function validateFx(fx) {
    var errors = [];
    if (!fx || Object.keys(fx).length === 0) {
      errors.push({ rowIdx: -1, field: "_fx", message: "汇率表不能为空" });
      return errors;
    }
    Object.keys(fx).forEach(function (cur) {
      var v = fx[cur];
      if (v == null || isNaN(Number(v)) || Number(v) <= 0) {
        errors.push({ rowIdx: -1, field: cur, message: "汇率 " + cur + "=" + v + " 无效（必须 > 0）" });
      }
    });
    return errors;
  }

  // 合并 household + cashflow + fx 校验
  function validateAll(household, cashflow, fx) {
    return {
      household: validateHousehold(household, fx),
      cashflow: validateCashflow(cashflow, fx),
      fx: validateFx(fx),
    };
  }

  // ============================================================
  // 导出
  // ============================================================

  root.Engine = {
    DEFAULT_FX: DEFAULT_FX,
    DEFAULT_LIMITS: DEFAULT_LIMITS,
    SCENARIOS: SCENARIOS,
    DEMO_HOUSEHOLD: DEMO_HOUSEHOLD,
    DEMO_CASHFLOW: DEMO_CASHFLOW,
    toHkd: toHkd,
    applyFx: applyFx,
    computeMetrics: computeMetrics,
    checkAllLimits: checkAllLimits,
    compareScenarios: compareScenarios,
    worst: worst,
    RANK: RANK,
    // 校验
    validateHousehold: validateHousehold,
    validateCashflow: validateCashflow,
    validateFx: validateFx,
    validateAll: validateAll,
  };
})(typeof window !== "undefined" ? window : globalThis);
