const DATA_URL = "data.json";
const numberFormat = new Intl.NumberFormat("en-US");
const $ = (id) => document.getElementById(id);

function formatNumber(value) {
  return Number.isFinite(Number(value)) ? numberFormat.format(Number(value)) : "—";
}
function formatTime(value) {
  if (!value) return "Waiting for first sync";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Recently";
  return date.toLocaleString([], { month:"short", day:"numeric", hour:"numeric", minute:"2-digit" });
}
function setText(id, value) { const node = $(id); if (node) node.textContent = value; }

function drawChart(points) {
  const svg = $("ccuChart");
  if (!svg) return;
  const valid = (points || []).filter(p => Number.isFinite(Number(p.ccu)));
  if (valid.length < 2) {
    svg.innerHTML = '<text x="360" y="115" text-anchor="middle" class="chart-empty">Collecting player history… check back soon.</text>';
    setText("ccuPoints", valid.length ? "1 data point" : "No history yet");
    return;
  }
  const recent = valid.filter(p => Date.now() - new Date(p.time).getTime() <= 24*60*60*1000);
  const data = recent.length > 1 ? recent : valid.slice(-100);
  const values = data.map(p => Number(p.ccu));
  const min = Math.min(0, ...values);
  const max = Math.max(5, ...values);
  const span = Math.max(1, max - min);
  const x = i => 8 + (i / Math.max(1, data.length - 1)) * 704;
  const y = v => 202 - ((v - min) / span) * 180;
  const line = data.map((p,i) => (i ? "L" : "M") + x(i).toFixed(1) + " " + y(Number(p.ccu)).toFixed(1)).join(" ");
  const area = line + " L 712 208 L 8 208 Z";
  const grid = [25,75,125,175].map(v => '<line class="grid-line" x1="8" y1="'+v+'" x2="712" y2="'+v+'"/>').join("");
  svg.innerHTML = '<defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stop-color="#5795ff" stop-opacity=".28"/><stop offset="100%" stop-color="#5795ff" stop-opacity="0"/></linearGradient></defs>' +
    grid + '<path class="chart-area" d="'+area+'"/><path class="chart-line" d="'+line+'"/>' +
    '<circle cx="'+x(data.length-1)+'" cy="'+y(values[values.length-1])+'" r="4.5" fill="#8db9ff" stroke="#111827" stroke-width="2"/>';
  setText("ccuPoints", data.length + " samples");
}

function updateMilestones(ccu) {
  [50,75,100].forEach(target => {
    const reached = ccu >= target;
    setText("milestone"+target, reached ? "Reached" : "In progress");
    const bar = $("bar"+target);
    if (bar) bar.style.width = Math.min(100, (ccu / target) * 100) + "%";
  });
}
function renderAnalytics(analytics) {
  const has = analytics && analytics.enabled;
  ["revenueStatus","dauStatus","retentionStatus"].forEach(id => setText(id, has ? "CONNECTED" : "API KEY NEEDED"));
  if (!has) return;
  const revenue = analytics.DailyRevenue || [];
  const dau = analytics.DailyActiveUsers || [];
  const d1 = analytics.ForwardD1Retention || [];
  const d7 = analytics.ForwardD7Retention || [];
  const d30 = analytics.ForwardD30Retention || [];
  const latest = list => list.length ? list[list.length-1].value : null;
  const rv = latest(revenue), dv = latest(dau);
  setText("revenueValue", rv == null ? "— R$" : formatNumber(rv) + " R$");
  setText("dauValue", dv == null ? "—" : formatNumber(dv));
  const percent = value => value == null ? "—" : (Number(value) <= 1 ? (Number(value)*100).toFixed(1) : Number(value).toFixed(1)) + "%";
  setText("d1Value", percent(latest(d1)));
  setText("d7Value", percent(latest(d7)));
  setText("d30Value", percent(latest(d30)));
  const newest = [...revenue,...dau,...d1,...d7,...d30].map(x=>x.time).sort().pop();
  if (newest) setText("revenueCaption", "Latest daily report · " + new Date(newest).toLocaleDateString());
}
function render(data) {
  const current = data.current || {};
  setText("gameName", current.name || "Click For Free");
  setText("ccuValue", formatNumber(current.ccu));
  setText("visitsValue", formatNumber(current.visits));
  setText("favoritesValue", formatNumber(current.favorites));
  setText("likesValue", formatNumber(current.likes));
  if (current.likes != null && current.dislikes != null && Number(current.likes)+Number(current.dislikes)>0) {
    const ratio = Number(current.likes)/(Number(current.likes)+Number(current.dislikes))*100;
    setText("likeRatio", ratio.toFixed(1) + "% positive rating");
  }
  setText("lastUpdated", formatTime(data.updatedAt));
  setText("ccuCaption", "Current concurrent users");
  updateMilestones(Number(current.ccu) || 0);
  drawChart(data.ccuHistory || []);
  renderAnalytics(data.analytics || {});
}
async function loadData(showToast=false) {
  const button = $("refreshButton");
  if (button) button.disabled = true;
  try {
    const response = await fetch(DATA_URL + "?v=" + Date.now(), { cache:"no-store" });
    if (!response.ok) throw new Error("Could not load dashboard data");
    render(await response.json());
    if (showToast) {
      const toast = $("toast");
      toast.textContent = "Dashboard refreshed";
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), 1800);
    }
  } catch (error) {
    console.error(error);
    if (showToast) {
      const toast = $("toast");
      toast.textContent = "Data refresh failed. Try again shortly.";
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), 2400);
    }
  } finally {
    if (button) button.disabled = false;
  }
}
$("refreshButton")?.addEventListener("click", () => loadData(true));
loadData();
setInterval(loadData, 60_000);
