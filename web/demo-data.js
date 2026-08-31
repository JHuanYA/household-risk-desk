/**
 * Demo 家庭数据（与 data/*.csv、data/Demo_Check.md 对齐）
 * 汇率：1 USD = 7.80 HKD，as_of = 2026-08-28
 *
 * 基准对账（误差应 < 1 HKD）：
 *   A = 6,106,000
 *   L = 2,445,000
 *   E = 3,661,000
 *   A_high = 119,000
 *   EXP_ess = 35,000
 *   DS = 21,000
 *   INC = 48,000
 *   LIM = 3.40 个月
 *   GAP = 91,000
 *   LEV = 40.04%
 *   DSTI = 43.75%
 *   房产/净值 = 150.23% → 红灯
 *   综合灯 = 红
 *
 * 用法（静态页，无需打包）：
 *   <script src="demo-data.js"></script>
 *   然后使用 window.DEMO
 */
(function (root) {
  const FX = {
    HKD: 1,
    USD: 7.8,
    CNY: 1.08,
    asOf: "2026-08-28",
  };

  function toHkd(amount, currency) {
    const rate = FX[currency];
    if (rate == null) {
      throw new Error("缺少汇率: " + currency);
    }
    return amount * rate;
  }

  const household = [
    {
      item_id: "CASH_HSBC",
      name: "汇丰港币活期",
      type: "asset",
      category: "cash",
      amount: 80000,
      currency: "HKD",
      liquidity: "high",
      owner: "本人",
      monthly_payment: null,
      note: "应急金主体",
    },
    {
      item_id: "CASH_USD_MM",
      name: "美元货币基金",
      type: "asset",
      category: "cash",
      amount: 5000,
      currency: "USD",
      liquidity: "high",
      owner: "本人",
      monthly_payment: null,
      note: "高流动性；按汇率折港币",
    },
    {
      item_id: "INV_HK",
      name: "港股及基金组合",
      type: "asset",
      category: "investment",
      amount: 350000,
      currency: "HKD",
      liquidity: "medium",
      owner: "本人",
      monthly_payment: null,
      note: "可变现但有价格波动，不得计入应急金",
    },
    {
      item_id: "INV_US",
      name: "美股ETF",
      type: "asset",
      category: "investment",
      amount: 15000,
      currency: "USD",
      liquidity: "medium",
      owner: "本人",
      monthly_payment: null,
      note: "可变现但有价格波动，不得计入应急金",
    },
    {
      item_id: "PROP_HOME",
      name: "自住物业估值",
      type: "asset",
      category: "property",
      amount: 5500000,
      currency: "HKD",
      liquidity: "low",
      owner: "共同",
      monthly_payment: null,
      note: "自住房；可变现差，不得当现金",
    },
    {
      item_id: "OTHER_MPF",
      name: "强积金估算",
      type: "asset",
      category: "other",
      amount: 20000,
      currency: "HKD",
      liquidity: "low",
      owner: "本人",
      monthly_payment: null,
      note: "提取受限",
    },
    {
      item_id: "LIAB_MTG",
      name: "住宅按揭余额",
      type: "liability",
      category: "mortgage",
      amount: 2400000,
      currency: "HKD",
      liquidity: null,
      owner: "共同",
      monthly_payment: 18000,
      note: "供款以现金流表为准",
    },
    {
      item_id: "LIAB_CC",
      name: "信用卡应还余额",
      type: "liability",
      category: "consumer",
      amount: 45000,
      currency: "HKD",
      liquidity: null,
      owner: "本人",
      monthly_payment: 3000,
      note: "计划还款额见现金流",
    },
  ].map(function (row) {
    return Object.assign({}, row, { hkd: toHkd(row.amount, row.currency) });
  });

  const cashflow = [
    {
      item_id: "INC_SALARY",
      name: "主职月薪",
      direction: "in",
      monthly_amount: 48000,
      currency: "HKD",
      essential: 0,
      debt_service: 0,
      source_rank: 1,
      note: "唯一收入来源",
    },
    {
      item_id: "OUT_MTG",
      name: "按揭供款",
      direction: "out",
      monthly_amount: 18000,
      currency: "HKD",
      essential: 1,
      debt_service: 1,
      source_rank: null,
      note: "必要支出且计入DSTI",
    },
    {
      item_id: "OUT_CC",
      name: "信用卡计划还款",
      direction: "out",
      monthly_amount: 3000,
      currency: "HKD",
      essential: 1,
      debt_service: 1,
      source_rank: null,
      note: "必要支出且计入DSTI",
    },
    {
      item_id: "OUT_FOOD",
      name: "食杂",
      direction: "out",
      monthly_amount: 8000,
      currency: "HKD",
      essential: 1,
      debt_service: 0,
      source_rank: null,
      note: "必要生活支出",
    },
    {
      item_id: "OUT_UTIL",
      name: "水电煤及网络",
      direction: "out",
      monthly_amount: 2500,
      currency: "HKD",
      essential: 1,
      debt_service: 0,
      source_rank: null,
      note: "必要生活支出",
    },
    {
      item_id: "OUT_TRANS",
      name: "交通",
      direction: "out",
      monthly_amount: 2000,
      currency: "HKD",
      essential: 1,
      debt_service: 0,
      source_rank: null,
      note: "必要生活支出",
    },
    {
      item_id: "OUT_INS",
      name: "保险",
      direction: "out",
      monthly_amount: 1500,
      currency: "HKD",
      essential: 1,
      debt_service: 0,
      source_rank: null,
      note: "必要支出",
    },
    {
      item_id: "OUT_DINE",
      name: "外出用餐",
      direction: "out",
      monthly_amount: 4000,
      currency: "HKD",
      essential: 0,
      debt_service: 0,
      source_rank: null,
      note: "非必要，不进流动性分母",
    },
    {
      item_id: "OUT_SUB",
      name: "订阅与娱乐",
      direction: "out",
      monthly_amount: 800,
      currency: "HKD",
      essential: 0,
      debt_service: 0,
      source_rank: null,
      note: "非必要",
    },
  ].map(function (row) {
    return Object.assign({}, row, {
      hkd: toHkd(row.monthly_amount, row.currency),
    });
  });

  const LIMITS = {
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

  const RANK = { green: 0, yellow: 1, red: 2 };

  function worst(a, b) {
    return RANK[a] >= RANK[b] ? a : b;
  }

  function compute(householdRows, cashflowRows, shock) {
    shock = shock || {};
    const incomeMult = shock.income_mult == null ? 1 : shock.income_mult;
    const essMult = shock.essential_exp_mult == null ? 1 : shock.essential_exp_mult;
    const investMult = shock.invest_mult == null ? 1 : shock.invest_mult;
    const propertyMult = shock.property_mult == null ? 1 : shock.property_mult;
    const dsMult = shock.debt_service_mult == null ? 1 : shock.debt_service_mult;
    const liabMult = shock.liability_mult == null ? 1 : shock.liability_mult;

    const assets = householdRows.filter(function (r) {
      return r.type === "asset";
    });
    const liabs = householdRows.filter(function (r) {
      return r.type === "liability";
    });

    function assetHkd(r) {
      if (r.category === "investment") return r.hkd * investMult;
      if (r.category === "property") return r.hkd * propertyMult;
      return r.hkd;
    }

    const A = assets.reduce(function (s, r) {
      return s + assetHkd(r);
    }, 0);
    const L = liabs.reduce(function (s, r) {
      return s + r.hkd * liabMult;
    }, 0);
    const E = A - L;
    const A_high = assets
      .filter(function (r) {
        return r.liquidity === "high";
      })
      .reduce(function (s, r) {
        return s + r.hkd;
      }, 0);
    const A_invest = assets
      .filter(function (r) {
        return r.category === "investment";
      })
      .reduce(function (s, r) {
        return s + assetHkd(r);
      }, 0);
    const A_property = assets
      .filter(function (r) {
        return r.category === "property";
      })
      .reduce(function (s, r) {
        return s + assetHkd(r);
      }, 0);
    const A_cash = assets
      .filter(function (r) {
        return r.category === "cash";
      })
      .reduce(function (s, r) {
        return s + r.hkd;
      }, 0);
    const A_other = assets
      .filter(function (r) {
        return r.category === "other";
      })
      .reduce(function (s, r) {
        return s + r.hkd;
      }, 0);

    const catTotals = {};
    assets.forEach(function (r) {
      const v = assetHkd(r);
      catTotals[r.category] = (catTotals[r.category] || 0) + v;
    });
    let maxCat = null;
    let maxCatAmt = 0;
    Object.keys(catTotals).forEach(function (k) {
      if (catTotals[k] > maxCatAmt) {
        maxCatAmt = catTotals[k];
        maxCat = k;
      }
    });

    const INC = cashflowRows
      .filter(function (r) {
        return r.direction === "in";
      })
      .reduce(function (s, r) {
        return s + r.hkd * incomeMult;
      }, 0);
    const EXP_ess = cashflowRows
      .filter(function (r) {
        return r.direction === "out" && r.essential === 1;
      })
      .reduce(function (s, r) {
        const m = r.debt_service === 1 ? dsMult * essMult : essMult;
        return s + r.hkd * m;
      }, 0);
    const DS = cashflowRows
      .filter(function (r) {
        return r.direction === "out" && r.debt_service === 1;
      })
      .reduce(function (s, r) {
        return s + r.hkd * dsMult;
      }, 0);
    const EXP_all = cashflowRows
      .filter(function (r) {
        return r.direction === "out";
      })
      .reduce(function (s, r) {
        if (r.debt_service === 1) return s + r.hkd * dsMult * (r.essential === 1 ? essMult : 1);
        if (r.essential === 1) return s + r.hkd * essMult;
        return s + r.hkd;
      }, 0);

    const ranks = {};
    cashflowRows.forEach(function (r) {
      if (r.direction === "in" && r.hkd * incomeMult > 0 && r.source_rank != null) {
        ranks[r.source_rank] = true;
      }
    });
    const incomeSources = Object.keys(ranks).length;

    const limAvailable = EXP_ess > 0;
    const LIM = limAvailable ? A_high / EXP_ess : null;
    const GAP = limAvailable
      ? Math.max(0, LIMITS.lim_target_months * EXP_ess - A_high)
      : null;
    const LEV = A > 0 ? L / A : Infinity;
    const DSTI = INC > 0 ? DS / INC : DS > 0 ? Infinity : null;
    const investRatio = E > 0 ? A_invest / E : null;
    const propertyRatio = E > 0 ? A_property / E : null;
    const maxCatRatio = E > 0 ? maxCatAmt / E : null;

    function limStatus() {
      if (!limAvailable) return "red";
      if (LIM < LIMITS.lim_red_below) return "red";
      if (LIM < LIMITS.lim_yellow_below) return "yellow";
      return "green";
    }
    function levStatus() {
      if (!isFinite(LEV) || LEV > LIMITS.lev_red_above) return "red";
      if (LEV > LIMITS.lev_yellow_above) return "yellow";
      return "green";
    }
    function equityStatus() {
      return E < 0 ? "red" : "green";
    }
    function dstiStatus() {
      if (DSTI == null) return "red";
      if (!isFinite(DSTI) || DSTI > LIMITS.dsti_red_above) return "red";
      if (DSTI > LIMITS.dsti_yellow_above) return "yellow";
      return "green";
    }
    function investStatus() {
      if (E <= 0) return "red";
      if (investRatio > LIMITS.invest_red_above) return "red";
      if (investRatio > LIMITS.invest_yellow_above) return "yellow";
      return "green";
    }
    function concStatus() {
      if (E <= 0) return "red";
      if (maxCatRatio > LIMITS.concentration_red_above) return "red";
      if (maxCatRatio > LIMITS.concentration_yellow_above) return "yellow";
      return "green";
    }
    function incomeStatus() {
      if (incomeSources <= 1 && limAvailable && LIM < 3) return "red";
      if (incomeSources <= 1 && limAvailable && LIM < 6) return "yellow";
      return "green";
    }

    const limits = [
      {
        id: "LIM",
        name: "流动性月数",
        value: LIM,
        unit: "月",
        yellow: "< 6",
        red: "< 3",
        status: limStatus(),
        reason: limAvailable
          ? "高流动性资产可覆盖 " +
            LIM.toFixed(2) +
            " 个月必要支出，目标 " +
            LIMITS.lim_target_months +
            " 个月"
          : "必要支出未录入，流动性指标不可用",
      },
      {
        id: "LEV",
        name: "杠杆 L/A",
        value: LEV,
        unit: "%",
        yellow: "> 40%",
        red: "> 60%",
        status: levStatus(),
        reason: "负债占总资产 " + (isFinite(LEV) ? (LEV * 100).toFixed(2) + "%" : "无穷大"),
      },
      {
        id: "E",
        name: "净值",
        value: E,
        unit: "HKD",
        yellow: "—",
        red: "< 0",
        status: equityStatus(),
        reason: E < 0 ? "净资产为负，已触发偿付危机定义" : "净资产为正",
      },
      {
        id: "DSTI",
        name: "偿债比率 DSTI",
        value: DSTI,
        unit: "%",
        yellow: "> 40%",
        red: "> 50%",
        status: dstiStatus(),
        reason:
          DSTI == null
            ? "收入为 0，DSTI 不适用"
            : !isFinite(DSTI)
              ? "收入为 0 但仍有供款"
              : "月供款占收入 " + (DSTI * 100).toFixed(2) + "%",
      },
      {
        id: "INVEST",
        name: "投资 / 净值",
        value: investRatio,
        unit: "%",
        yellow: "> 60%",
        red: "> 80%",
        status: investStatus(),
        reason:
          E <= 0
            ? "净值不为正，集中度不输出百分比"
            : "投资类资产占净值 " + (investRatio * 100).toFixed(2) + "%",
      },
      {
        id: "CONC",
        name: "单一类别 / 净值",
        value: maxCatRatio,
        unit: "%",
        yellow: "> 70%",
        red: "> 90%",
        status: concStatus(),
        reason:
          E <= 0
            ? "净值不为正，集中度不输出百分比"
            : "类别 " + maxCat + " 占净值 " + (maxCatRatio * 100).toFixed(2) + "%",
      },
      {
        id: "INCOME",
        name: "收入单一性",
        value: incomeSources,
        unit: "条",
        yellow: "来源≤1 且 LIM<6",
        red: "来源≤1 且 LIM<3",
        status: incomeStatus(),
        reason:
          "收入来源 " +
          incomeSources +
          " 条" +
          (limAvailable ? "，流动性 " + LIM.toFixed(2) + " 个月" : ""),
      },
    ];

    let overall = "green";
    limits.forEach(function (x) {
      overall = worst(overall, x.status);
    });

    const alerts = limits.filter(function (x) {
      return x.status !== "green";
    });

    return {
      A: A,
      L: L,
      E: E,
      A_high: A_high,
      A_cash: A_cash,
      A_invest: A_invest,
      A_property: A_property,
      A_other: A_other,
      maxCat: maxCat,
      maxCatAmt: maxCatAmt,
      INC: INC,
      EXP_ess: EXP_ess,
      EXP_all: EXP_all,
      DS: DS,
      CF: INC - EXP_all,
      incomeSources: incomeSources,
      LIM: LIM,
      LID: LIM == null ? null : LIM * 30,
      GAP: GAP,
      LEV: LEV,
      DSTI: DSTI,
      investRatio: investRatio,
      propertyRatio: propertyRatio,
      maxCatRatio: maxCatRatio,
      limits: limits,
      alerts: alerts,
      overall: overall,
      unemployment: {
        need3: EXP_ess * 3,
        need6: EXP_ess * 6,
        gap3: Math.max(0, EXP_ess * 3 - A_high),
        gap6: Math.max(0, EXP_ess * 6 - A_high),
        monthsCovered: LIM,
      },
    };
  }

  const SCENARIOS = [
    {
      id: "base",
      name: "基准",
      income_mult: 1,
      essential_exp_mult: 1,
      invest_mult: 1,
      property_mult: 1,
      debt_service_mult: 1,
      liability_mult: 1,
    },
    {
      id: "jobloss3",
      name: "失业 3 个月视角",
      income_mult: 0,
      essential_exp_mult: 1,
      invest_mult: 1,
      property_mult: 1,
      debt_service_mult: 1,
      liability_mult: 1,
    },
    {
      id: "jobloss6",
      name: "失业 6 个月视角",
      income_mult: 0,
      essential_exp_mult: 1,
      invest_mult: 1,
      property_mult: 1,
      debt_service_mult: 1,
      liability_mult: 1,
    },
    {
      id: "invest20",
      name: "投资下跌 20%",
      income_mult: 1,
      essential_exp_mult: 1,
      invest_mult: 0.8,
      property_mult: 1,
      debt_service_mult: 1,
      liability_mult: 1,
    },
    {
      id: "invest40",
      name: "投资下跌 40%",
      income_mult: 1,
      essential_exp_mult: 1,
      invest_mult: 0.6,
      property_mult: 1,
      debt_service_mult: 1,
      liability_mult: 1,
    },
    {
      id: "property15",
      name: "房价下跌 15%",
      income_mult: 1,
      essential_exp_mult: 1,
      invest_mult: 1,
      property_mult: 0.85,
      debt_service_mult: 1,
      liability_mult: 1,
    },
    {
      id: "property30",
      name: "房价下跌 30%",
      income_mult: 1,
      essential_exp_mult: 1,
      invest_mult: 1,
      property_mult: 0.7,
      debt_service_mult: 1,
      liability_mult: 1,
    },
    {
      id: "rate20",
      name: "供款上升 20%",
      income_mult: 1,
      essential_exp_mult: 1,
      invest_mult: 1,
      property_mult: 1,
      debt_service_mult: 1.2,
      liability_mult: 1,
    },
    {
      id: "combo_job_invest",
      name: "联合：失业+投资下跌20%",
      income_mult: 0,
      essential_exp_mult: 1,
      invest_mult: 0.8,
      property_mult: 1,
      debt_service_mult: 1,
      liability_mult: 1,
      defaultSelected: true,
    },
    {
      id: "combo_housing",
      name: "联合：失业+房价-15%+供款+20%",
      income_mult: 0,
      essential_exp_mult: 1,
      invest_mult: 1,
      property_mult: 0.85,
      debt_service_mult: 1.2,
      liability_mult: 1,
    },
  ];

  const baseline = compute(household, cashflow, {});

  const DEMO = {
    meta: {
      mode: "Demo",
      householdName: "香港演示家庭",
      asOf: "2026-08-28",
      reportingCurrency: "HKD",
      disclaimer: "虚构数据，仅供演示。不构成投资、信贷或税务建议。",
    },
    fx: FX,
    limitsConfig: LIMITS,
    household: household,
    cashflow: cashflow,
    baseline: baseline,
    scenarios: SCENARIOS,
    toHkd: toHkd,
    compute: function (scenarioId) {
      const sc =
        SCENARIOS.filter(function (s) {
          return s.id === scenarioId;
        })[0] || SCENARIOS[0];
      return {
        scenario: sc,
        metrics: compute(household, cashflow, sc),
      };
    },
  };

  root.DEMO = DEMO;
})(typeof window !== "undefined" ? window : globalThis);
