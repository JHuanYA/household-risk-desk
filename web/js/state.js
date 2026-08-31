/**
 * 状态管理 —— localStorage 持久化 + 响应式重算 + 输入校验
 * 命名空间: window.App
 *
 * 用法:
 *   App.init()                      // 启动时调用，加载数据并算一次
 *   App.setHousehold(rows)          // 改资产负债表（自动校验）
 *   App.setCashflow(rows)           // 改现金流（自动校验）
 *   App.setFx(rates)                // 改汇率（自动校验）
 *   App.resetToDemo()               // 重置为 Demo
 *   App.onChange(function(){...})   // 订阅变化
 *   App.current                     // 当前 state
 *     .errors = { household, cashflow, fx }  // 校验结果
 *     .hasErrors                    // 是否有任何校验错误
 */
(function (root) {
  "use strict";

  var LS_KEY = "household_risk_desk_v1";
  var _listeners = [];

  var state = {
    household: [],
    cashflow: [],
    fx: {},
    metrics: null,
    limits: null,
    errors: { household: [], cashflow: [], fx: [] },
  };

  function _emit() {
    for (var i = 0; i < _listeners.length; i++) {
      try { _listeners[i](state); } catch (e) { console.error("listener error:", e); }
    }
  }

  function _validateAll() {
    var E = root.Engine;
    state.errors = E.validateAll(state.household, state.cashflow, state.fx);
  }

  function _recalc() {
    var E = root.Engine;
    _validateAll();

    // 如果有以下致命错误，跳过计算，避免产生 NaN/Infinity
    var fxFatal = state.errors.fx.length > 0;
    var incomeRows = state.cashflow.filter(function (r) { return r.direction === "in" && Number(r.monthly_amount) > 0; });
    var noIncome = incomeRows.length === 0;

    // household/cashflow 里的 amount 类错误（负数 / NaN / 总额为0）
    var hasAmountErr = state.errors.household.some(function (e) {
      return e.field === "amount" || e.field === "_total";
    });
    hasAmountErr = hasAmountErr || state.errors.cashflow.some(function (e) {
      return e.field === "monthly_amount";
    });

    if (fxFatal || noIncome || hasAmountErr) {
      state.metrics = null;
      state.limits = null;
      return;
    }

    try {
      var applied = E.applyFx(state.household, state.cashflow, state.fx);
      state.metrics = E.computeMetrics(applied.household, applied.cashflow, {});
      state.limits = E.checkAllLimits(state.metrics);
    } catch (e) {
      console.error("computeMetrics failed:", e);
      state.metrics = null;
      state.limits = null;
    }
  }

  function _save() {
    try {
      var payload = {
        household: state.household,
        cashflow: state.cashflow,
        fx: state.fx,
      };
      localStorage.setItem(LS_KEY, JSON.stringify(payload));
    } catch (e) { console.warn("localStorage save failed:", e); }
  }

  function _load() {
    try {
      var raw = localStorage.getItem(LS_KEY);
      if (raw) {
        var payload = JSON.parse(raw);
        if (payload.household) state.household = payload.household;
        if (payload.cashflow) state.cashflow = payload.cashflow;
        if (payload.fx) state.fx = payload.fx;
        return true;
      }
    } catch (e) { console.warn("localStorage load failed:", e); }
    return false;
  }

  // ============= 公共 API =============

  function init() {
    if (!_load()) {
      resetToDemo();
      return;
    }
    _recalc();
    _emit();
  }

  function resetToDemo() {
    var E = root.Engine;
    state.household = JSON.parse(JSON.stringify(E.DEMO_HOUSEHOLD));
    state.cashflow = JSON.parse(JSON.stringify(E.DEMO_CASHFLOW));
    state.fx = JSON.parse(JSON.stringify(E.DEFAULT_FX));
    _save();
    _recalc();
    _emit();
  }

  function setHousehold(rows) {
    state.household = rows;
    _save();
    _recalc();
    _emit();
  }

  function setCashflow(rows) {
    state.cashflow = rows;
    _save();
    _recalc();
    _emit();
  }

  function setFx(rates) {
    state.fx = rates;
    _save();
    _recalc();
    _emit();
  }

  // 内部操作（增删行）—— 先改数组再调用 set
  function addHouseholdRow(row) {
    var copy = JSON.parse(JSON.stringify(state.household));
    copy.push(row);
    setHousehold(copy);
  }
  function removeHouseholdRow(idx) {
    var copy = JSON.parse(JSON.stringify(state.household));
    copy.splice(idx, 1);
    setHousehold(copy);
  }
  function updateHouseholdCell(idx, key, val) {
    var copy = JSON.parse(JSON.stringify(state.household));
    copy[idx][key] = val;
    setHousehold(copy);
  }
  function addCashflowRow(row) {
    var copy = JSON.parse(JSON.stringify(state.cashflow));
    copy.push(row);
    setCashflow(copy);
  }
  function removeCashflowRow(idx) {
    var copy = JSON.parse(JSON.stringify(state.cashflow));
    copy.splice(idx, 1);
    setCashflow(copy);
  }
  function updateCashflowCell(idx, key, val) {
    var copy = JSON.parse(JSON.stringify(state.cashflow));
    copy[idx][key] = val;
    setCashflow(copy);
  }

  function onChange(fn) { _listeners.push(fn); }

  // 计算属性：是否有任何校验错误
  function _hasErrors() {
    return state.errors.household.length > 0 ||
           state.errors.cashflow.length > 0 ||
           state.errors.fx.length > 0;
  }

  root.App = {
    init: init,
    resetToDemo: resetToDemo,
    setHousehold: setHousehold,
    setCashflow: setCashflow,
    setFx: setFx,
    addHouseholdRow: addHouseholdRow,
    removeHouseholdRow: removeHouseholdRow,
    updateHouseholdCell: updateHouseholdCell,
    addCashflowRow: addCashflowRow,
    removeCashflowRow: removeCashflowRow,
    updateCashflowCell: updateCashflowCell,
    onChange: onChange,
    get current() { return state; },
    get hasErrors() { return _hasErrors(); },
  };
})(typeof window !== "undefined" ? window : globalThis);
