document.addEventListener("DOMContentLoaded", () => {
    let allAlerts = [];
    let currentFilter = "ALL";
    let searchQuery = "";
    let reconnectDelay = 1000;
    let reconnectTimer = null;

    const apiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.hostname}:8000/ws`;

    const statusElement = document.getElementById("connection-status");
    const tableBody = document.getElementById("alerts-table-body");
    const totalAlertsEl = document.getElementById("total-alerts");
    const highAlertsEl = document.getElementById("high-alerts");
    const lastEventTimeEl = document.getElementById("last-event-time");
    const searchInput = document.getElementById("ip-search-input");
    const topIpsListEl = document.getElementById("top-ips-list");
    const exportButton = document.getElementById("export-csv-button");
    const btnAll = document.getElementById("filter-all");
    const btnBrute = document.getElementById("filter-brute");
    const btnSpray = document.getElementById("filter-spray");

    const severityClasses = {
        HIGH: "bg-red-500/10 text-red-400 border-red-500/20",
        MEDIUM: "bg-orange-500/10 text-orange-400 border-orange-500/20",
        LOW: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    };
    const typeClasses = {
        BRUTE_FORCE: "bg-red-500/10 text-red-400 border-red-500/20",
        PASSWORD_SPRAYING: "bg-purple-500/10 text-purple-400 border-purple-500/20",
        SUSPICIOUS_SUCCESS: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    };

    function setConnectionStatus(label, className) {
        if (!statusElement) return;
        statusElement.textContent = label;
        statusElement.className = `text-xs font-medium px-3 py-1.5 rounded-full border ${className}`;
    }

    function connectWebSocket() {
        const ws = new WebSocket(wsUrl);
        ws.onopen = () => {
            reconnectDelay = 1000;
            setConnectionStatus("WebSocket: connected", "text-emerald-400 bg-slate-800/80 border-slate-700/50");
        };
        ws.onmessage = (event) => {
            try {
                const alertData = JSON.parse(event.data);
                const key = alertKey(alertData);
                if (!allAlerts.some((item) => alertKey(item) === key)) {
                    allAlerts.unshift(alertData);
                    allAlerts = allAlerts.slice(0, 200);
                }
                render();
            } catch (error) {
                console.error("Invalid WebSocket alert payload", error);
            }
        };
        ws.onerror = () => ws.close();
        ws.onclose = () => {
            setConnectionStatus("WebSocket: reconnecting…", "text-amber-400 bg-slate-800/80 border-slate-700/50");
            if (reconnectTimer) clearTimeout(reconnectTimer);
            reconnectTimer = setTimeout(connectWebSocket, reconnectDelay);
            reconnectDelay = Math.min(reconnectDelay * 2, 15000);
        };
    }

    function alertKey(alert) {
        const parsedTime = alert.timestamp ? new Date(alert.timestamp).getTime() : NaN;
        const timestampKey = Number.isNaN(parsedTime) ? String(alert.timestamp || "") : String(parsedTime);
        return [timestampKey, alert.alert_type, alert.username, alert.ip_address, alert.failed_attempts].join("|");
    }

    if (searchInput) {
        searchInput.addEventListener("input", (event) => {
            searchQuery = event.target.value.trim().toLowerCase();
            render();
        });
    }
    if (btnAll) btnAll.addEventListener("click", () => setFilter("ALL"));
    if (btnBrute) btnBrute.addEventListener("click", () => setFilter("BRUTE_FORCE"));
    if (btnSpray) btnSpray.addEventListener("click", () => setFilter("PASSWORD_SPRAYING"));
    if (exportButton) exportButton.addEventListener("click", () => {
        window.location.href = `${apiBase}/api/export/csv`;
    });

    function setFilter(filterType) {
        currentFilter = filterType;
        const inactive = "px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 transition";
        [btnAll, btnBrute, btnSpray].forEach((button) => {
            if (button) button.className = inactive;
        });
        if (filterType === "ALL" && btnAll) btnAll.className = "px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white transition shadow-lg shadow-blue-500/20";
        if (filterType === "BRUTE_FORCE" && btnBrute) btnBrute.className = "px-4 py-2 text-xs font-semibold rounded-lg bg-red-600 text-white transition shadow-lg shadow-red-500/20";
        if (filterType === "PASSWORD_SPRAYING" && btnSpray) btnSpray.className = "px-4 py-2 text-xs font-semibold rounded-lg bg-purple-600 text-white transition shadow-lg shadow-purple-500/20";
        render();
    }

    function updateTopIps(alerts) {
        if (!topIpsListEl) return;
        const counts = new Map();
        alerts.forEach((alert) => {
            if (alert.ip_address) counts.set(alert.ip_address, (counts.get(alert.ip_address) || 0) + 1);
        });
        const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3);
        topIpsListEl.replaceChildren();
        if (sorted.length === 0) {
            const empty = document.createElement("span");
            empty.className = "text-slate-500";
            empty.textContent = "Нет данных";
            topIpsListEl.appendChild(empty);
            return;
        }
        sorted.forEach(([ip, count]) => {
            const row = document.createElement("div");
            row.className = "flex justify-between items-center bg-slate-800/60 px-2 py-1 rounded";
            const ipText = document.createElement("span");
            ipText.className = "text-slate-200";
            ipText.textContent = ip;
            const countText = document.createElement("span");
            countText.className = "bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded font-bold";
            countText.textContent = `${count} инц.`;
            row.append(ipText, countText);
            topIpsListEl.appendChild(row);
        });
    }

    function makeCell(text, className) {
        const cell = document.createElement("td");
        cell.className = className;
        cell.textContent = text == null || text === "" ? "—" : String(text);
        return cell;
    }

    function makeBadge(text, className) {
        const badge = document.createElement("span");
        badge.className = `px-2.5 py-1 rounded-full text-xs font-semibold border ${className}`;
        badge.textContent = text;
        return badge;
    }

    function render() {
        if (!tableBody) return;
        const filteredAlerts = allAlerts.filter((alert) => {
            const matchesType = currentFilter === "ALL" || alert.alert_type === currentFilter;
            const haystack = [alert.ip_address, alert.username, alert.alert_type, alert.severity]
                .filter(Boolean).join(" ").toLowerCase();
            return matchesType && (searchQuery === "" || haystack.includes(searchQuery));
        });

        updateTopIps(allAlerts);
        tableBody.replaceChildren();
        if (filteredAlerts.length === 0) {
            const row = document.createElement("tr");
            const cell = document.createElement("td");
            cell.colSpan = 6;
            cell.className = "px-6 py-8 text-center text-slate-500";
            cell.textContent = "Инциденты не найдены…";
            row.appendChild(cell);
            tableBody.appendChild(row);
        } else {
            filteredAlerts.forEach((alert) => {
                const row = document.createElement("tr");
                row.className = "hover:bg-slate-800/50 transition border-b border-slate-800/50";
                const time = alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : "—";
                row.appendChild(makeCell(time, "px-6 py-4 text-slate-300 font-mono text-xs"));

                const typeCell = document.createElement("td");
                typeCell.className = "px-6 py-4";
                typeCell.appendChild(makeBadge(alert.alert_type || "UNKNOWN", typeClasses[alert.alert_type] || "bg-slate-500/10 text-slate-300 border-slate-500/20"));
                row.appendChild(typeCell);

                const severity = String(alert.severity || "LOW").toUpperCase();
                const severityCell = document.createElement("td");
                severityCell.className = "px-6 py-4";
                severityCell.appendChild(makeBadge(severity, severityClasses[severity] || "bg-slate-500/10 text-slate-300 border-slate-500/20"));
                row.appendChild(severityCell);
                row.appendChild(makeCell(alert.username, "px-6 py-4 font-mono text-slate-200"));
                row.appendChild(makeCell(alert.ip_address, "px-6 py-4 font-mono text-slate-300"));
                row.appendChild(makeCell(alert.failed_attempts ?? 0, "px-6 py-4 font-bold text-orange-400"));
                tableBody.appendChild(row);
            });
        }

        // KPI cards report the loaded alert set, not the current filtered subset.
        if (totalAlertsEl) totalAlertsEl.textContent = String(allAlerts.length);
        if (highAlertsEl) highAlertsEl.textContent = String(allAlerts.filter((a) => String(a.severity).toUpperCase() === "HIGH").length);
        const newest = allAlerts[0];
        if (lastEventTimeEl) lastEventTimeEl.textContent = newest?.timestamp ? new Date(newest.timestamp).toLocaleTimeString() : "Ожидание событий…";
    }

    async function loadAlertHistory() {
        try {
            const response = await fetch(`${apiBase}/api/alerts`);
            if (!response.ok) throw new Error(`Alert history request failed: ${response.status}`);
            const history = await response.json();
            const existing = new Map(allAlerts.map((alert) => [alertKey(alert), alert]));
            history.forEach((alert) => existing.set(alertKey(alert), alert));
            allAlerts = [...existing.values()].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 200);
            render();
        } catch (error) {
            console.error("Could not load alert history", error);
        }
    }

    connectWebSocket();
    loadAlertHistory();
});
