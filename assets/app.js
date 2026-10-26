/* 社科大讲座汇 · 前端渲染与交互 */
(function () {
  "use strict";

  var DATA = window.UCASS_DATA || null;
  var WEEK = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
  var PAGE_SIZE = 12;
  var UNDATED_LIMIT = 6;

  var state = {
    q: "",
    campus: "",
    type: "",
    org: "",
    period: "all",
    date: "",
    sort: "default",
    limit: PAGE_SIZE,
    calYear: 0,
    calMonth: 0,
    openId: "",
  };

  var lastPage = "list";
  var currentPage = "list";

  /* ---------------- 工具 ---------------- */
  function $(id) {
    return document.getElementById(id);
  }

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function pad(n) {
    return n < 10 ? "0" + n : String(n);
  }

  function isoOf(d) {
    return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate());
  }

  function todayISO() {
    return isoOf(new Date());
  }

  function parseISO(value) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || "");
    if (!m) return null;
    return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  }

  function daysFromToday(value) {
    var d = parseISO(value);
    if (!d) return null;
    var t = parseISO(todayISO());
    return Math.round((d - t) / 86400000);
  }

  function weekdayOf(value) {
    var d = parseISO(value);
    return d ? WEEK[d.getDay()] : "";
  }

  function clampText(text, max) {
    text = String(text || "").replace(/\s+/g, " ").trim();
    return text.length > max ? text.slice(0, max - 1) + "…" : text;
  }

  function displayTitle(raw) {
    var t = String(raw || "").replace(/\s+/g, " ").trim();
    t = t.replace(/^(?:讲座预告|讲座回顾|活动预告|活动回顾|学术预告|学术讲座|学术动态|会议预告|论坛预告|报名)\s*[|｜丨:：]\s*/, "");
    t = t.replace(/^(?:讲座预告|讲座回顾|活动预告|活动回顾)\s+/, "");
    return t;
  }

  function typeClass(type) {
    if (!type) return "";
    if (type.indexOf("沙龙") >= 0) return "salon";
    if (type.indexOf("工作坊") >= 0) return "workshop";
    if (type.indexOf("论坛") >= 0 || type.indexOf("研讨") >= 0) return "forum";
    if (type.indexOf("报告会") >= 0) return "report";
    return "";
  }

  function campusClass(campus) {
    if (campus === "良乡校区") return "liangxiang";
    if (campus === "望京校区") return "wangjing";
    if (campus === "线上") return "online";
    return "";
  }

  function kindLabel(kind) {
    if (kind === "review") return "回顾";
    if (kind === "preview") return "预告";
    return "";
  }

  function statusOf(item) {
    var diff = daysFromToday(item.event_date);
    if (diff === null) return { cls: "", text: "日期待定" };
    if (diff === 0) return { cls: "today", text: "今天" };
    if (diff === 1) return { cls: "upcoming", text: "明天" };
    if (diff > 1) return { cls: "upcoming", text: diff + " 天后" };
    return { cls: "past", text: "已结束" };
  }

  function fmtGenerated(value) {
    var m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(value || "");
    if (!m) return value || "—";
    return m[1] + "-" + m[2] + "-" + m[3] + " " + m[4] + ":" + m[5];
  }

  function fmtDate(value) {
    if (!value) return "日期待定";
    return value.replace(/-/g, ".") + " " + weekdayOf(value);
  }

  /* ---------------- 数据整理 ---------------- */
  var LECTURES = [];
  var MONTHS = [];

  function prepare() {
    if (!DATA) return;
    LECTURES = (DATA.lectures || []).map(function (item) {
      var copy = {};
      Object.keys(item).forEach(function (k) {
        copy[k] = item[k];
      });
      copy.title = item.title || "未命名活动";
      copy.display_title = displayTitle(copy.title);
      copy.tag_list = Array.isArray(item.tags) ? item.tags : [];
      return copy;
    });
  }

  function byId(id) {
    for (var i = 0; i < LECTURES.length; i += 1) {
      if (LECTURES[i].id === id) return LECTURES[i];
    }
    return null;
  }

  function upcomingSorted() {
    return LECTURES.filter(function (item) {
      var diff = daysFromToday(item.event_date);
      return diff !== null && diff >= 0;
    }).sort(function (a, b) {
      return a.event_date < b.event_date ? -1 : a.event_date > b.event_date ? 1 : 0;
    });
  }

  /* ---------------- 筛选 ---------------- */
  function matches(item) {
    if (state.campus && item.campus !== state.campus) return false;
    if (state.type && item.type !== state.type) return false;
    if (state.org && item.organizer !== state.org) return false;
    if (state.date && item.event_date !== state.date) return false;

    var diff = daysFromToday(item.event_date);
    if (state.period === "upcoming" && !(diff !== null && diff >= 0)) return false;
    if (state.period === "week") {
      if (diff === null || diff < 0 || diff > 7) return false;
    }
    if (state.period === "month") {
      if (!item.event_date) return false;
      var now = new Date();
      if (item.event_date.slice(0, 7) !== now.getFullYear() + "-" + pad(now.getMonth() + 1)) return false;
    }
    if (state.period === "year") {
      if (!item.event_date || item.event_date.slice(0, 4) !== String(new Date().getFullYear())) return false;
    }

    if (state.q) {
      var q = state.q.toLowerCase();
      var haystack = [
        item.title, item.speaker, item.organizer, item.source_name, item.location,
        item.type, item.summary, item.section, (item.tag_list || []).join(" "),
      ].join(" ").toLowerCase();
      if (haystack.indexOf(q) < 0) return false;
    }
    return true;
  }

  function filtered() {
    var list = LECTURES.filter(matches);
    var mode = state.sort;
    list.sort(function (a, b) {
      if (mode === "date-desc") {
        return (b.event_date || "").localeCompare(a.event_date || "");
      }
      if (mode === "date-asc") {
        return (a.event_date || "9999").localeCompare(b.event_date || "9999");
      }
      if (mode === "published") {
        return (b.published || "").localeCompare(a.published || "");
      }
      var da = daysFromToday(a.event_date);
      var db = daysFromToday(b.event_date);
      var ga = da === null ? 2 : da >= 0 ? 0 : 1;
      var gb = db === null ? 2 : db >= 0 ? 0 : 1;
      if (ga !== gb) return ga - gb;
      if (ga === 0) return (a.event_date || "").localeCompare(b.event_date || "");
      if (ga === 1) return (b.event_date || "").localeCompare(a.event_date || "");
      return (b.published || "").localeCompare(a.published || "");
    });
    return list;
  }

  /* ---------------- 卡片 ---------------- */
  function cardHTML(item) {
    var date = item.event_date;
    var rail = date
      ? '<div class="date-rail"><span class="date-month">' + esc(date.slice(5, 7)) + " 月</span>" +
        '<span class="date-day">' + esc(date.slice(8, 10)) + "</span>" +
        '<span class="date-week">' + esc(weekdayOf(date)) + "</span></div>"
      : '<div class="date-rail date-unknown"><span class="date-month">日期</span>' +
        '<span class="date-day">待定</span></div>';

    var badges = '<span class="badge type ' + typeClass(item.type) + '">' + esc(item.type || "学术活动") + "</span>";
    if (item.campus) {
      badges += '<span class="badge campus ' + campusClass(item.campus) + '">' + esc(item.campus) + "</span>";
    }
    var kind = kindLabel(item.content_kind);
    if (kind) badges += '<span class="badge kind">' + kind + "</span>";

    var st = statusOf(item);
    badges += '<span class="card-status ' + st.cls + '">' + st.text + "</span>";

    var meta = [];
    if (item.speaker) meta.push('<span>主讲 ' + esc(item.speaker) + "</span>");
    if (item.organizer) meta.push("<span>" + esc(clampText(item.organizer, 26)) + "</span>");
    if (item.location) meta.push("<span>" + esc(clampText(item.location, 26)) + "</span>");
    if (item.time_text) meta.push("<span>" + esc(item.time_text) + "</span>");

    var summary = item.summary ? '<p class="card-summary">' + esc(clampText(item.summary, 120)) + "</p>" : "";

    return '<article class="lecture-card" tabindex="0" role="button" data-id="' + esc(item.id) + '" aria-label="' +
      esc(item.display_title) + '">' + rail +
      '<div class="card-body"><div class="card-top">' + badges + "</div>" +
      '<h3 class="lecture-title">' + esc(clampText(item.display_title, 78)) + "</h3>" +
      (meta.length ? '<div class="card-meta">' + meta.join("") + "</div>" : "") +
      summary +
      '<div class="card-foot"><span>' + (item.published ? esc(item.published) + " 发布" : "发布日期未注明") + "</span>" +
      '<span class="source">' + esc(item.source_name || "") + "</span>" +
      '<span class="go">查看详情 →</span></div></div></article>';
  }

  function renderList() {
    var wrap = $("listResults");
    var summary = $("resultsSummary");
    var loadWrap = $("loadMoreWrap");

    if (!LECTURES.length) {
      wrap.innerHTML = '<div class="empty-state"><div class="empty-glyph">空</div><h3>数据尚未载入</h3>' +
        '<p>请确认 data/site_data.js 存在，或先运行 python crawler/crawl.py 生成数据。</p></div>';
      summary.textContent = "暂无数据";
      loadWrap.hidden = true;
      return;
    }

    var list = filtered();
    renderActiveFilters();

    var totalLiangxiang = list.filter(function (x) { return x.campus === "良乡校区"; }).length;
    var online = list.filter(function (x) { return x.campus === "线上"; }).length;
    summary.innerHTML = "共 <strong>" + list.length + "</strong> 场活动" +
      (totalLiangxiang ? " · 良乡 " + totalLiangxiang + " 场" : "") +
      (online ? " · 线上 " + online + " 场" : "");

    if (!list.length) {
      wrap.innerHTML = '<div class="empty-state"><div class="empty-glyph">无</div><h3>没有匹配的活动</h3>' +
        '<p>试试减少筛选条件，或换一个关键词。</p><button class="btn-ghost btn-sm" type="button" data-action="reset">重置筛选</button></div>';
      $("loadMoreWrap").hidden = true;
      return;
    }

    var upcoming = [];
    var past = [];
    var undated = [];
    list.forEach(function (item) {
      var diff = daysFromToday(item.event_date);
      if (diff === null) undated.push(item);
      else if (diff >= 0) upcoming.push(item);
      else past.push(item);
    });

    var html = "";
    if (upcoming.length) {
      html += '<div class="result-section"><div class="result-heading"><h3>即将开始</h3>' +
        '<span class="count">' + upcoming.length + " 场</span><span class=\"line\"></span></div>" +
        upcoming.map(cardHTML).join("") + "</div>";
    }

    if (undated.length) {
      var shownUndated = undated.slice(0, UNDATED_LIMIT);
      html += '<div class="result-section"><div class="result-heading"><h3>日期待定</h3>' +
        '<span class="count">' + shownUndated.length + " / " + undated.length + " 场</span><span class=\"line\"></span></div>" +
        shownUndated.map(cardHTML).join("") +
        (undated.length > shownUndated.length
          ? '<p class="results-hint" style="margin-top:10px">仅展示前 ' + UNDATED_LIMIT + " 场日期待定的活动，可用关键词进一步查找。</p>"
          : "") + "</div>";
    }

    if (past.length) {
      var shown = past.slice(0, state.limit);
      html += '<div class="result-section"><div class="result-heading"><h3>往期活动</h3>' +
        '<span class="count">' + shown.length + " / " + past.length + " 场</span><span class=\"line\"></span></div>";
      var lastMonth = "";
      shown.forEach(function (item) {
        var month = item.event_date ? item.event_date.slice(0, 7) : "";
        if (month && month !== lastMonth) {
          html += '<div class="month-divider">' + month.replace("-", " 年 ") + " 月</div>";
          lastMonth = month;
        }
        html += cardHTML(item);
      });
      html += "</div>";

      loadWrap = $("loadMoreWrap");
      loadWrap.hidden = past.length <= state.limit;
      var btn = $("loadMore");
      btn.textContent = "加载更多往期活动（还有 " + (past.length - state.limit) + " 场）";
    } else {
      $("loadMoreWrap").hidden = true;
    }

    wrap.innerHTML = html;
    if (undated.length && !past.length && !upcoming.length) {
      // 只有日期待定活动时也保证有内容
    }
  }

  function renderActiveFilters() {
    var box = $("activeFilters");
    var pills = [];
    if (state.q) pills.push(["搜索", state.q, "q"]);
    if (state.campus) pills.push(["校区", state.campus, "campus"]);
    if (state.type) pills.push(["类型", state.type, "type"]);
    if (state.org) pills.push(["主办", state.org, "org"]);
    if (state.date) pills.push(["日期", state.date, "date"]);
    if (state.period !== "all") {
      var labels = { upcoming: "即将开始", week: "本周", month: "本月", year: "今年" };
      pills.push(["时间", labels[state.period] || state.period, "period"]);
    }

    if (!pills.length) {
      box.hidden = true;
      box.innerHTML = "";
      return;
    }
    box.hidden = false;
    box.innerHTML = '<span class="active-label">当前筛选</span>' + pills.map(function (p) {
      return '<span class="active-pill">' + esc(p[0]) + "：" + esc(p[1]) +
        '<button type="button" data-clear="' + p[2] + '" aria-label="移除筛选">×</button></span>';
    }).join("");
  }

  /* ---------------- 筛选控件 ---------------- */
  function buildFilters() {
    var campusCount = {};
    LECTURES.forEach(function (item) {
      campusCount[item.campus] = (campusCount[item.campus] || 0) + 1;
    });
    var campi = ["良乡校区", "望京校区", "线上", "未注明", "校外"];
    $("campusFilter").innerHTML = ['<button class="filter-chip active" type="button" data-campus="">全部</button>']
      .concat(campi.filter(function (c) { return campusCount[c]; }).map(function (c) {
        return '<button class="filter-chip" type="button" data-campus="' + esc(c) + '">' + esc(c) +
          '<span class="num">' + campusCount[c] + "</span></button>";
      })).join("");

    var types = {};
    LECTURES.forEach(function (item) {
      types[item.type] = (types[item.type] || 0) + 1;
    });
    $("typeFilter").innerHTML = '<option value="">全部类型</option>' +
      Object.keys(types).sort(function (a, b) { return types[b] - types[a]; }).map(function (t) {
        return '<option value="' + esc(t) + '">' + esc(t) + "（" + types[t] + "）</option>";
      }).join("");

    var orgs = {};
    LECTURES.forEach(function (item) {
      if (item.organizer) orgs[item.organizer] = (orgs[item.organizer] || 0) + 1;
    });
    $("orgFilter").innerHTML = '<option value="">全部主办单位</option>' +
      Object.keys(orgs).sort(function (a, b) { return orgs[b] - orgs[a]; }).slice(0, 80).map(function (o) {
        return '<option value="' + esc(o) + '">' + esc(clampText(o, 24)) + "（" + orgs[o] + "）</option>";
      }).join("");

    var periods = [["all", "全部"], ["upcoming", "即将开始"], ["week", "本周"], ["month", "本月"], ["year", "今年"]];
    $("periodFilter").innerHTML = periods.map(function (p) {
      return '<button class="filter-chip' + (p[0] === "all" ? " active" : "") + '" type="button" data-period="' +
        p[0] + '">' + p[1] + "</button>";
    }).join("");
  }

  /* ---------------- 日历 ---------------- */
  function eventsOn(dateStr) {
    return LECTURES.filter(function (item) {
      return item.event_date === dateStr;
    });
  }

  function initCalendar() {
    var upcoming = upcomingSorted();
    var base = upcoming.length ? parseISO(upcoming[0].event_date) : new Date();
    state.calYear = base.getFullYear();
    state.calMonth = base.getMonth();
  }

  function renderCalendar() {
    var y = state.calYear;
    var m = state.calMonth;
    $("calMonthTitle").textContent = y + " 年 " + (m + 1) + " 月";

    var first = new Date(y, m, 1);
    var offset = (first.getDay() + 6) % 7;
    var daysInMonth = new Date(y, m + 1, 0).getDate();
    var rows = Math.ceil((offset + daysInMonth) / 7);
    var today = todayISO();
    var cells = [];

    for (var i = 0; i < rows * 7; i += 1) {
      var dayNum = i - offset + 1;
      var cellDate = new Date(y, m, dayNum);
      var dateStr = isoOf(cellDate);
      var outside = dayNum < 1 || dayNum > daysInMonth;
      var events = outside ? [] : eventsOn(dateStr);
      var classes = ["cal-cell"];
      if (outside) classes.push("outside");
      if (dateStr === today) classes.push("today");
      if (events.length) classes.push("has-event");

      var inner = '<div class="cal-day">' + cellDate.getDate() + "</div>";
      events.slice(0, 3).forEach(function (item) {
        var cls = "cal-event";
        var tc = typeClass(item.type);
        if (tc) cls += " type-" + tc;
        if (item.campus === "线上") cls += " type-online";
        inner += '<button class="' + cls + '" type="button" data-id="' + esc(item.id) + '" title="' +
          esc(item.display_title) + '">' + esc(clampText(item.display_title, 18)) + "</button>";
      });
      if (events.length > 3) inner += '<div class="cal-more">+' + (events.length - 3) + " 场</div>";

      cells.push('<div class="' + classes.join(" ") + '" data-date="' + (outside ? "" : dateStr) + '">' + inner + "</div>");
    }

    $("calGrid").innerHTML = cells.join("");

    var monthEvents = LECTURES.filter(function (item) {
      return item.event_date && item.event_date.slice(0, 7) === y + "-" + pad(m + 1);
    });
    $("calCount").textContent = "本月 " + monthEvents.length + " 场";

    var liangxiang = monthEvents.filter(function (x) { return x.campus === "良乡校区"; }).length;
    var online = monthEvents.filter(function (x) { return x.campus === "线上"; }).length;
    var orgs = {};
    monthEvents.forEach(function (x) { if (x.source_name) orgs[x.source_name] = 1; });
    $("calSideStats").innerHTML =
      '<div class="side-stat"><strong>' + monthEvents.length + "</strong><span>本月场次</span></div>" +
      '<div class="side-stat"><strong>' + liangxiang + "</strong><span>良乡校区</span></div>" +
      '<div class="side-stat"><strong>' + online + "</strong><span>线上活动</span></div>" +
      '<div class="side-stat"><strong>' + Object.keys(orgs).length + "</strong><span>覆盖单位</span></div>";

    var sorted = monthEvents.slice().sort(function (a, b) {
      return (a.event_date || "").localeCompare(b.event_date || "");
    });
    $("calMiniList").innerHTML = sorted.length
      ? sorted.slice(0, 10).map(function (item) {
        return '<button class="mini-item" type="button" data-id="' + esc(item.id) + '">' +
          '<span class="mini-date">' + esc(item.event_date.slice(5).replace("-", ".")) + " " +
          esc(weekdayOf(item.event_date)) + "</span>" +
          '<span class="mini-title">' + esc(clampText(item.display_title, 32)) + "</span></button>";
      }).join("")
      : '<p class="mini-empty">本月暂无收录活动。</p>';
  }

  /* ---------------- 来源矩阵 ---------------- */
  function renderSources() {
    var sources = DATA.sources || [];
    var accounts = DATA.accounts || [];

    var listingCount = 0;
    sources.forEach(function (s) { listingCount += (s.listings || []).length; });
    var wechat = accounts.filter(function (a) { return a.platform === "微信公众号"; }).length;
    var douyin = accounts.filter(function (a) { return a.platform === "抖音"; }).length;

    $("sourceSummary").innerHTML =
      '<div class="ss-item"><strong>' + sources.length + "</strong><span>来源单位</span></div>" +
      '<div class="ss-item"><strong>' + listingCount + "</strong><span>官网栏目</span></div>" +
      '<div class="ss-item"><strong>' + wechat + "</strong><span>公众号入口</span></div>" +
      '<div class="ss-item"><strong>' + douyin + "</strong><span>抖音入口</span></div>";

    var groups = { "校级": [], "学院": [] };
    sources.forEach(function (s) {
      (groups[s.category] || (groups[s.category] = [])).push(s);
    });

    $("sourceGroups").innerHTML = Object.keys(groups).map(function (name) {
      var cards = groups[name].map(function (s) {
        var listings = (s.listings || []).map(function (l) {
          return '<div class="listing-row"><a href="' + esc(l.url) + '" target="_blank" rel="noopener">' +
            esc(l.section) + "</a><span class=\"listing-kept\">" + (l.kept || 0) + " 条</span></div>";
        }).join("");
        return '<div class="source-card"><div class="source-card-top">' +
          '<span class="source-name">' + esc(s.name) + "</span>" +
          '<a class="source-home" href="' + esc(s.homepage) + '" target="_blank" rel="noopener">官网 ↗</a></div>' +
          '<div class="source-count-row"><span class="source-count">' + (s.count || 0) +
          '</span><span class="source-count-unit">条活动</span></div>' +
          '<div class="source-listings">' + (listings || '<span class="source-empty">暂无可用栏目</span>') + "</div></div>";
      }).join("");
      return '<div class="source-group"><p class="source-group-title">' + esc(name) + "</p>" +
        '<div class="source-grid">' + cards + "</div></div>";
    }).join("");

    var platforms = {};
    accounts.forEach(function (a) {
      (platforms[a.platform] || (platforms[a.platform] = [])).push(a);
    });
    $("accountGroups").innerHTML = Object.keys(platforms).map(function (platform) {
      var cards = platforms[platform].map(function (a) {
        var isDouyin = a.platform === "抖音";
        var handle = a.handle || "";
        return '<div class="account-card' + (isDouyin ? " douyin" : "") + '">' +
          '<span class="account-platform">' + (isDouyin ? "抖音" : "微信") + "</span>" +
          '<div class="account-body"><span class="account-name">' + esc(a.name) + "</span>" +
          '<p class="account-meta">' + esc(a.org || "") + (handle ? " · " + esc(handle) : "") + "</p>" +
          '<p class="account-note-text">' + esc(a.note || "") + "</p></div>" +
          (isDouyin && a.search_url
            ? '<a class="account-action" href="' + esc(a.search_url) + '" target="_blank" rel="noopener">站内搜索</a>'
            : '<button class="account-action" type="button" data-copy-account="' + esc(handle || a.name) + '">复制</button>') +
          "</div>";
      }).join("");
      return '<div class="account-group"><p class="source-group-title">' + esc(platform) + "</p>" +
        '<div class="account-grid">' + cards + "</div></div>";
    }).join("");
  }

  /* ---------------- 详情抽屉 ---------------- */
  function openDrawer(id) {
    var item = byId(id);
    var drawer = $("detailDrawer");
    var overlay = $("drawerOverlay");
    var content = $("drawerContent");
    if (!item) {
      content.innerHTML = '<div class="drawer-empty">未找到这条活动，可能已被移除。</div>';
    } else {
      content.innerHTML = drawerHTML(item);
    }
    state.openId = id || "";
    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden", "false");
    overlay.classList.add("open");
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeDrawer(restoreHash) {
    var drawer = $("detailDrawer");
    var overlay = $("drawerOverlay");
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden", "true");
    overlay.classList.remove("open");
    overlay.hidden = true;
    document.body.style.overflow = "";
    state.openId = "";
    if (restoreHash && /^#\/lecture\//.test(location.hash)) {
      location.hash = "#/" + lastPage;
    }
  }

  function drawerHTML(item) {
    var badges = '<span class="badge type ' + typeClass(item.type) + '">' + esc(item.type || "学术活动") + "</span>";
    if (item.campus) badges += '<span class="badge campus ' + campusClass(item.campus) + '">' + esc(item.campus) + "</span>";
    var kind = kindLabel(item.content_kind);
    if (kind) badges += '<span class="badge kind">' + kind + "</span>";

    var rows = [];
    rows.push(["日期", fmtDate(item.event_date) + (item.time_text ? " · " + esc(item.time_text) : "")]);
    rows.push(["地点", item.location ? esc(item.location) : "未注明"]);
    if (item.speaker) rows.push(["主讲人", esc(item.speaker)]);
    rows.push(["主办", esc(item.organizer || item.source_name || "未注明")]);
    rows.push(["来源", esc(item.source_name || "") + (item.section ? " · " + esc(item.section) : "")]);
    if (item.published) rows.push(["发布", esc(item.published)]);
    if (item.event_date) {
      var st = statusOf(item);
      rows.push(["状态", esc(st.text)]);
    }

    var tags = (item.tag_list || []).length
      ? '<div class="detail-row"><span class="detail-label">主题</span><span class="detail-value"><span class="detail-tags">' +
        item.tag_list.map(function (t) { return '<span class="detail-tag">' + esc(t) + "</span>"; }).join("") +
        "</span></span></div>"
      : "";

    return '<div class="drawer-eyebrow">' + badges + "</div>" +
      '<h2 class="drawer-title">' + esc(item.display_title) + "</h2>" +
      '<div class="detail-grid">' + rows.map(function (r) {
        return '<div class="detail-row"><span class="detail-label">' + r[0] + '</span><span class="detail-value">' + r[1] + "</span></div>";
      }).join("") + tags + "</div>" +
      (item.summary ? '<h3 class="drawer-section-title">摘要</h3><p class="drawer-summary">' + esc(item.summary) + "</p>" : "") +
      (item.excerpt ? '<h3 class="drawer-section-title">原文摘录</h3><p class="drawer-excerpt">' + esc(clampText(item.excerpt, 1200)) + "</p>" : "") +
      '<div class="drawer-actions"><a class="btn-primary" href="' + esc(item.url) + '" target="_blank" rel="noopener">阅读原文 ↗</a>' +
      '<button class="btn-copy" type="button" data-copy-link="' + esc(item.url) + '">复制原文链接</button></div>' +
      '<p class="drawer-source-note">内容来自公开网页，版权归主办单位与原作者所有。信息以原文为准。</p>';
  }

  /* ---------------- 首屏 ---------------- */
  function renderHero() {
    if (!DATA) {
      $("heroNote").textContent = "数据文件未载入：请确认 data/site_data.js 存在。";
      return;
    }
    var meta = DATA.meta || {};
    var generated = fmtGenerated(meta.generated_at);
    $("headerUpdated").textContent = generated;
    $("footerUpdated").textContent = generated;
    $("aboutGenerated").textContent = generated;

    $("heroNote").textContent = "已收录 " + (meta.total || LECTURES.length) + " 场活动，覆盖 " +
      (meta.sources_count || 0) + " 个单位 · 良乡 " + (meta.liangxiang || 0) + " 场 · 数据生成于 " + generated;

    var stats = {
      total: meta.total || LECTURES.length,
      liangxiang: meta.liangxiang || LECTURES.filter(function (x) { return x.campus === "良乡校区"; }).length,
      upcoming: upcomingSorted().length,
      sources: meta.sources_count || 0,
    };
    Object.keys(stats).forEach(function (k) {
      document.querySelectorAll('[data-stat="' + k + '"]').forEach(function (el) {
        el.textContent = stats[k];
      });
    });

    var months = {};
    LECTURES.forEach(function (item) {
      if (item.event_date) months[item.event_date.slice(0, 7)] = 1;
    });
    MONTHS = Object.keys(months).sort();
    $("aboutAccounts").textContent = (DATA.accounts || []).length;
    $("aboutMonths").textContent = MONTHS.length;

    var next = upcomingSorted()[0];
    if (!next) {
      next = LECTURES.filter(function (x) { return x.event_date; }).sort(function (a, b) {
        return (b.event_date || "").localeCompare(a.event_date || "");
      })[0];
    }
    if (!next) {
      $("nextEvent").innerHTML = '<div class="next-skeleton">暂无活动数据</div>';
      return;
    }
    var d = parseISO(next.event_date);
    $("nextEvent").innerHTML =
      '<div class="next-top"><span class="next-label">' + (d && next.event_date >= todayISO() ? "NEXT LECTURE" : "最近收录") +
      '</span><span class="next-kind">' + esc(next.type || "学术活动") + "</span></div>" +
      '<div class="next-date-row"><div><div class="next-day">' + (d ? pad(d.getDate()) : "—") + "</div>" +
      '<div class="next-month">' + (d ? d.getFullYear() + " / " + pad(d.getMonth() + 1) : "日期待定") + "</div></div>" +
      '<span class="next-weekday">' + (d ? WEEK[d.getDay()] : "") + "</span></div>" +
      '<h2 class="next-title">' + esc(clampText(next.display_title, 64)) + "</h2>" +
      '<div class="next-meta">' +
      (next.speaker ? "<span>主讲 " + esc(next.speaker) + "</span>" : "") +
      (next.location ? "<span>" + esc(clampText(next.location, 20)) + "</span>" : "") +
      (next.time_text ? "<span>" + esc(next.time_text) + "</span>" : "") +
      "</div>" +
      '<button class="next-link" type="button" data-id="' + esc(next.id) + '">查看详情 →</button>';
  }

  /* ---------------- 页面与路由 ---------------- */
  function showPage(name) {
    currentPage = name;
    ["list", "calendar", "sources", "about"].forEach(function (p) {
      var el = $("page-" + p);
      if (el) el.hidden = p !== name;
    });
    document.querySelectorAll(".main-nav a").forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("data-nav") === name);
    });
    document.querySelectorAll(".view-btn").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-view") === name);
    });
    lastPage = name;
    if (name === "list") renderList();
    if (name === "calendar") renderCalendar();
    window.scrollTo({ top: 0, behavior: "auto" });
    $("mainNav").classList.remove("open");
    $("navToggle").setAttribute("aria-expanded", "false");
  }

  function onHashChange() {
    var hash = location.hash || "#/list";
    var lecture = /^#\/lecture\/(.+)$/.exec(hash);
    if (lecture) {
      var id = decodeURIComponent(lecture[1]);
      if (state.openId !== id) openDrawer(id);
      return;
    }
    if (currentPage === "list" || currentPage === "calendar") {
      // 保持当前视图，由下方路由决定
    }
    var name = hash.replace(/^#\/?/, "").split("?")[0] || "list";
    if (["list", "calendar", "sources", "about"].indexOf(name) < 0) name = "list";
    if (state.openId) closeDrawer(false);
    if (name !== currentPage) showPage(name);
    else lastPage = name;
  }

  function applyQuick(kind) {
    state.limit = PAGE_SIZE;
    if (kind === "liangxiang") {
      state.campus = state.campus === "良乡校区" ? "" : "良乡校区";
    } else if (kind === "online") {
      state.campus = state.campus === "线上" ? "" : "线上";
    } else if (kind === "week") {
      state.period = state.period === "week" ? "all" : "week";
    } else if (kind === "salon") {
      state.type = state.type === "学术沙龙" ? "" : "学术沙龙";
    } else if (kind === "ai") {
      state.q = state.q === "人工智能" ? "" : "人工智能";
      $("heroSearch").value = state.q;
      $("filterSearch").value = state.q;
    }
    syncControls();
    renderList();
  }

  function syncControls() {
    $("campusFilter").querySelectorAll("[data-campus]").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-campus") === state.campus);
    });
    $("periodFilter").querySelectorAll("[data-period]").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-period") === state.period);
    });
    $("typeFilter").value = state.type;
    $("orgFilter").value = state.org;
    $("sortFilter").value = state.sort;
    document.querySelectorAll("[data-quick]").forEach(function (b) {
      var kind = b.getAttribute("data-quick");
      var active = (kind === "liangxiang" && state.campus === "良乡校区") ||
        (kind === "online" && state.campus === "线上") ||
        (kind === "week" && state.period === "week") ||
        (kind === "salon" && state.type === "学术沙龙") ||
        (kind === "ai" && state.q === "人工智能");
      b.classList.toggle("active", !!active);
    });
  }

  function resetAll() {
    state.q = "";
    state.campus = "";
    state.type = "";
    state.org = "";
    state.period = "all";
    state.date = "";
    state.sort = "default";
    state.limit = PAGE_SIZE;
    $("heroSearch").value = "";
    $("filterSearch").value = "";
    syncControls();
    renderList();
  }

  function copyText(text, button) {
    var done = function () {
      if (!button) return;
      var old = button.textContent;
      button.textContent = "已复制";
      setTimeout(function () { button.textContent = old; }, 1400);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(function () { fallbackCopy(text); done(); });
    } else {
      fallbackCopy(text);
      done();
    }
  }

  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try { document.execCommand("copy"); } catch (e) { /* ignore */ }
    document.body.removeChild(area);
  }

  /* ---------------- 事件绑定 ---------------- */
  function bind() {
    var headerSearch = $("heroSearch");
    var filterSearch = $("filterSearch");
    var timer = null;

    function updateQuery(value) {
      state.q = value.trim();
      state.limit = PAGE_SIZE;
      headerSearch.value = state.q;
      filterSearch.value = state.q;
      clearTimeout(timer);
      timer = setTimeout(function () {
        syncControls();
        renderList();
      }, 160);
    }

    headerSearch.addEventListener("input", function (e) { updateQuery(e.target.value); });
    filterSearch.addEventListener("input", function (e) { updateQuery(e.target.value); });

    document.addEventListener("keydown", function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (currentPage !== "list") location.hash = "#/list";
        headerSearch.focus();
        headerSearch.select();
      }
      if (e.key === "Escape" && state.openId) closeDrawer(true);
    });

    $("quickChips").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-quick]");
      if (!btn) return;
      applyQuick(btn.getAttribute("data-quick"));
    });

    $("campusFilter").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-campus]");
      if (!btn) return;
      state.campus = btn.getAttribute("data-campus");
      state.limit = PAGE_SIZE;
      syncControls();
      renderList();
    });

    $("periodFilter").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-period]");
      if (!btn) return;
      state.period = btn.getAttribute("data-period");
      state.date = "";
      state.limit = PAGE_SIZE;
      syncControls();
      renderList();
    });

    $("typeFilter").addEventListener("change", function (e) {
      state.type = e.target.value;
      state.limit = PAGE_SIZE;
      syncControls();
      renderList();
    });

    $("orgFilter").addEventListener("change", function (e) {
      state.org = e.target.value;
      state.limit = PAGE_SIZE;
      syncControls();
      renderList();
    });

    $("sortFilter").addEventListener("change", function (e) {
      state.sort = e.target.value;
      state.limit = PAGE_SIZE;
      renderList();
    });

    $("resetFilters").addEventListener("click", resetAll);

    $("activeFilters").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-clear]");
      if (!btn) return;
      var field = btn.getAttribute("data-clear");
      state.limit = PAGE_SIZE;
      if (field === "q") {
        state.q = "";
        headerSearch.value = "";
        filterSearch.value = "";
      } else if (field === "period") {
        state.period = "all";
      } else if (field === "date") {
        state.date = "";
      } else {
        state[field] = "";
      }
      syncControls();
      renderList();
    });

    $("listResults").addEventListener("click", function (e) {
      if (e.target.closest('[data-action="reset"]')) {
        resetAll();
        return;
      }
      var card = e.target.closest(".lecture-card");
      if (card) location.hash = "#/lecture/" + card.getAttribute("data-id");
    });

    $("listResults").addEventListener("keydown", function (e) {
      if (e.key !== "Enter" && e.key !== " ") return;
      var card = e.target.closest(".lecture-card");
      if (!card) return;
      e.preventDefault();
      location.hash = "#/lecture/" + card.getAttribute("data-id");
    });

    $("loadMore").addEventListener("click", function () {
      state.limit += PAGE_SIZE;
      renderList();
    });

    document.querySelectorAll(".view-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        location.hash = "#/" + btn.getAttribute("data-view");
      });
    });

    $("calPrev").addEventListener("click", function () {
      state.calMonth -= 1;
      if (state.calMonth < 0) { state.calMonth = 11; state.calYear -= 1; }
      renderCalendar();
    });

    $("calNext").addEventListener("click", function () {
      state.calMonth += 1;
      if (state.calMonth > 11) { state.calMonth = 0; state.calYear += 1; }
      renderCalendar();
    });

    $("calToday").addEventListener("click", function () {
      var now = new Date();
      state.calYear = now.getFullYear();
      state.calMonth = now.getMonth();
      renderCalendar();
    });

    $("calGrid").addEventListener("click", function (e) {
      var evt = e.target.closest(".cal-event");
      if (evt) {
        location.hash = "#/lecture/" + evt.getAttribute("data-id");
        return;
      }
      var cell = e.target.closest(".cal-cell");
      if (!cell || !cell.classList.contains("has-event")) return;
      var date = cell.getAttribute("data-date");
      if (!date) return;
      state.date = date;
      state.period = "all";
      state.limit = PAGE_SIZE;
      syncControls();
      location.hash = "#/list";
      if (currentPage === "list") renderList();
    });

    $("calMiniList").addEventListener("click", function (e) {
      var item = e.target.closest(".mini-item");
      if (item) location.hash = "#/lecture/" + item.getAttribute("data-id");
    });

    $("nextEvent").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-id]");
      if (btn) location.hash = "#/lecture/" + btn.getAttribute("data-id");
    });

    $("accountGroups").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-copy-account]");
      if (btn) copyText(btn.getAttribute("data-copy-account"), btn);
    });

    $("drawerContent").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-copy-link]");
      if (btn) copyText(btn.getAttribute("data-copy-link"), btn);
    });

    $("drawerClose").addEventListener("click", function () { closeDrawer(true); });
    $("drawerOverlay").addEventListener("click", function () { closeDrawer(true); });

    $("navToggle").addEventListener("click", function () {
      var nav = $("mainNav");
      var open = nav.classList.toggle("open");
      $("navToggle").setAttribute("aria-expanded", String(open));
    });

    window.addEventListener("hashchange", onHashChange);
  }

  /* ---------------- 启动 ---------------- */
  function start() {
    prepare();
    if (!DATA) {
      renderHero();
      $("listResults").innerHTML = '<div class="empty-state"><div class="empty-glyph">缺</div><h3>缺少数据文件</h3>' +
        '<p>请先运行 <code>python crawler/crawl.py</code> 生成 data/site_data.js。</p></div>';
      return;
    }
    initCalendar();
    buildFilters();
    renderHero();
    syncControls();
    renderList();
    renderSources();
    bind();
    onHashChange();
  }

  function boot() {
    var proto = location.protocol;
    if (proto === "http:" || proto === "https:") {
      // 在线模式：动态拉取最新数据（定时爬取后由 Pages 重新发布），失败则回退到内嵌数据
      fetch("data/lectures.json?ts=" + Date.now())
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function (payload) {
          if (payload && payload.lectures) DATA = payload;
        })
        .catch(function () { /* 保持内嵌数据 */ })
        .then(start);
    } else {
      start();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
