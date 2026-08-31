/**
 * UI 工具 —— 数字格式化、灯号、卡片、图标
 * 命名空间: window.UI
 */
(function (root) {
  "use strict";

  // ============================================================
  // 数字格式化
  // ============================================================

  function hkd(v) {
    if (v == null) return "N/A";
    return "HK$" + Math.round(v).toLocaleString();
  }

  function hkdShort(v) {
    if (v == null) return "N/A";
    var a = Math.abs(v);
    if (a >= 1000000) return "HK$" + (v / 1000000).toFixed(2) + "M";
    if (a >= 1000) return "HK$" + (v / 1000).toFixed(0) + "K";
    return "HK$" + Math.round(v).toLocaleString();
  }

  function pct(v, digits) {
    if (v == null) return "N/A";
    if (!isFinite(v)) return "∞";
    digits = digits == null ? 1 : digits;
    return (v * 100).toFixed(digits) + "%";
  }

  function months(v) {
    if (v == null) return "N/A";
    if (!isFinite(v)) return "∞";
    return v.toFixed(2) + " 个月";
  }

  // ============================================================
  // 灯号颜色
  // ============================================================

  var STATUS_COLORS = {
    green: "#3FB950",
    yellow: "#F0B429",
    red: "#F85149",
  };
  var STATUS_LABELS = {
    green: "绿灯",
    yellow: "黄灯",
    red: "红灯",
  };

  function statusColor(s) { return STATUS_COLORS[s] || "#8B949E"; }
  function statusLabel(s) { return STATUS_LABELS[s] || s; }

  // ============================================================
  // HTML 片段生成器
  // ============================================================

  function lightPill(status, label) {
    var color = statusColor(status);
    var l = label || statusLabel(status);
    return '<span class="hf-pill" style="background:' + color + '22;border-color:' + color + ';color:' + color + '">' + l + '</span>';
  }

  function metricCard(label, value, hint, tone) {
    // tone: good / warn / bad / neutral
    var toneClass = "hf-tone-" + (tone || "neutral");
    return '<div class="hf-metric-card ' + toneClass + '">' +
      '<div class="hf-metric-label">' + label + '</div>' +
      '<div class="hf-metric-value">' + value + '</div>' +
      '<div class="hf-metric-hint">' + hint + '</div>' +
      '</div>';
  }

  function alertCard(status, name, reason) {
    var color = statusColor(status);
    return '<div class="hf-alert" style="border-left-color:' + color + '">' +
      '<div class="hf-alert-head"><span class="hf-dot" style="background:' + color + '"></span><b>' + name + '</b></div>' +
      '<div class="hf-alert-body">' + reason + '</div>' +
      '</div>';
  }

  function sectionTitle(title, rightHtml) {
    return '<div class="hf-section">' +
      '<div class="hf-section-title">' + title + '</div>' +
      (rightHtml ? '<div class="hf-section-right">' + rightHtml + '</div>' : '') +
      '</div>';
  }

  // ============================================================
  // 校验错误 UI
  // ============================================================

  /**
   * 生成一个红色错误横幅 + 错误列表
   * @param {Object} errors  { household: [], cashflow: [], fx: [] }
   * @param {String} scope   只展示特定表错误 (household / cashflow / fx / "all")
   */
  function errorBanner(errors, scope) {
    if (!errors) return "";
    var scopes = ["household", "cashflow", "fx"];
    var shown = scope && scope !== "all" ? [scope] : scopes;
    var hasAny = false;
    var items = [];
    shown.forEach(function (s) {
      var list = errors[s] || [];
      list.forEach(function (e) {
        hasAny = true;
        var rowLabel = e.rowIdx === -1 ? "" : ("第 " + (e.rowIdx + 1) + " 行 · ");
        items.push('<div class="hf-error-item">' + rowLabel + '<b>' + _scopeLabel(s) + '</b>: ' + e.message + '</div>');
      });
    });
    if (!hasAny) return "";
    return '<div class="hf-banner hf-banner-error">' +
      '<div class="hf-banner-title">⚠ 输入数据存在 ' + items.length + ' 个错误，以下指标可能不准确</div>' +
      items.join("") +
      '</div>';
  }

  function _scopeLabel(s) {
    return { household: "资产负债表", cashflow: "现金流表", fx: "汇率表" }[s] || s;
  }

  /**
   * 把 errors 数组转成 Map: { rowIdx: { field: true } }
   */
  function errorsByRow(errors) {
    var map = {};
    (errors || []).forEach(function (e) {
      var key = e.rowIdx;
      if (!map[key]) map[key] = {};
      map[key][e.field] = true;
    });
    return map;
  }

  // ============================================================
  // 可编辑表格
  // ============================================================

  /**
   * 生成一个可编辑表格
   * @param {Array} rows       数据行
   * @param {Array} columns    列定义 [{key, label, type, width, options}]
   * @param {Function} onChange  当任何单元格改动时触发 (rowsCopy) => void
   * @param {Function} onDeleteRow  删除行时触发 (rowIdx) => void
   * @param {Function} onAddRow    添加行时触发 () => void
   * @param {Array}  rowErrors     该表的 errors 数组（用于行级红色标记）
   */
  function editableTable(id, rows, columns, onChange, onDeleteRow, onAddRow, rowErrors) {
    var rowErrMap = errorsByRow(rowErrors || []);
    var html = '<div class="hf-editable-wrap"><table class="hf-editable" id="' + id + '"><thead><tr>';
    columns.forEach(function (c) {
      html += '<th style="width:' + (c.width || "auto") + '">' + c.label + '</th>';
    });
    if (onDeleteRow) html += '<th style="width:32px"></th>';
    html += '</tr></thead><tbody>';
    rows.forEach(function (row, idx) {
      var rowHasErr = rowErrMap[idx] || rowErrMap[-1];
      html += '<tr data-idx="' + idx + '"' + (rowHasErr ? ' class="hf-row-error"' : '') + '>';
      columns.forEach(function (c) {
        html += _renderCell(row, idx, c, rowErrMap[idx]);
      });
      if (onDeleteRow) {
        html += '<td><button class="hf-cell-btn hf-cell-del" data-del="' + idx + '" title="删除行">×</button></td>';
      }
      html += '</tr>';
    });
    html += '</tbody></table>';
    if (onAddRow) {
      html += '<div class="hf-editable-add"><button class="hf-btn hf-btn-secondary" data-add="1">＋ 添加一行</button></div>';
    }
    html += '</div>';
    return html;
  }

  function _renderCell(row, idx, col, fieldErrors) {
    var val = row[col.key];
    var type = col.type || "text";
    var attrs = 'data-key="' + col.key + '" data-idx="' + idx + '"';
    var errClass = fieldErrors && fieldErrors[col.key] ? " hf-input-error" : "";
    var cellClass = errClass ? ' class="hf-error-cell"' : '';
    if (type === "select" && col.options) {
      var opts = col.options.map(function (o) {
        var v = typeof o === "string" ? o : o.value;
        var label = typeof o === "string" ? o : o.label;
        return '<option value="' + v + '"' + (String(val) === String(v) ? " selected" : "") + '>' + label + '</option>';
      }).join("");
      return '<td' + cellClass + '><select class="hf-input hf-select' + errClass + '" ' + attrs + '>' + opts + '</select></td>';
    }
    if (type === "number") {
      var step = col.step || "1";
      var min = col.min != null ? ' min="' + col.min + '"' : "";
      var placeholder = col.placeholder != null ? ' placeholder="' + col.placeholder + '"' : "";
      return '<td' + cellClass + '><input type="number" step="' + step + '"' + min + placeholder + ' class="hf-input' + errClass + '" value="' + (val == null ? "" : val) + '" ' + attrs + '></td>';
    }
    if (type === "checkbox") {
      return '<td' + cellClass + '><input type="checkbox" class="hf-input' + errClass + '" value="1" ' + (val ? "checked" : "") + ' ' + attrs + '></td>';
    }
    // text
    return '<td' + cellClass + '><input type="text" class="hf-input' + errClass + '" value="' + (val == null ? "" : val) + '" ' + attrs + '></td>';
  }

  // 在 DOM 上绑定 editable table 的事件（一次性，在渲染后调用）
  function bindEditableTable(containerId, onChange, onDeleteRow, onAddRow) {
    var root = document.getElementById(containerId);
    if (!root) return;

    root.querySelectorAll("input, select").forEach(function (el) {
      el.addEventListener("change", function (ev) {
        var idx = parseInt(ev.target.dataset.idx, 10);
        var key = ev.target.dataset.key;
        var rows = root._rows || [];
        var copy = JSON.parse(JSON.stringify(rows));
        var newVal;
        if (ev.target.type === "number") newVal = ev.target.value === "" ? null : parseFloat(ev.target.value);
        else if (ev.target.type === "checkbox") newVal = ev.target.checked ? 1 : 0;
        else newVal = ev.target.value;
        copy[idx][key] = newVal;
        onChange(copy);
      });
    });

    root.querySelectorAll("[data-del]").forEach(function (btn) {
      btn.addEventListener("click", function (ev) {
        onDeleteRow(parseInt(ev.target.dataset.del, 10));
      });
    });

    var addBtn = root.querySelector("[data-add]");
    if (addBtn) {
      addBtn.addEventListener("click", function () { onAddRow(); });
    }
  }

  // 记录当前表格的 rows 引用（以便 input 改值时能取到最新数组）
  function setTableRows(containerId, rows) {
    var root = document.getElementById(containerId);
    if (root) root._rows = rows;
  }

  // ============================================================
  // 导出
  // ============================================================

  root.UI = {
    hkd: hkd, hkdShort: hkdShort, pct: pct, months: months,
    statusColor: statusColor, statusLabel: statusLabel,
    STATUS_COLORS: STATUS_COLORS,
    lightPill: lightPill, metricCard: metricCard, alertCard: alertCard, sectionTitle: sectionTitle,
    editableTable: editableTable, bindEditableTable: bindEditableTable, setTableRows: setTableRows,
    // 校验错误 UI
    errorBanner: errorBanner, errorsByRow: errorsByRow,
  };
})(typeof window !== "undefined" ? window : globalThis);
