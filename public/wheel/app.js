(function () {
    'use strict';

    const STORAGE_KEY = 'wheelStrategyData_v1';

    /** @type {{positions: Array<Object>, holdings: Object, prices: Object, manualSales: Array<Object>}} */
    let state = loadState();

    function loadState() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (raw) {
                const parsed = JSON.parse(raw);
                return {
                    positions: parsed.positions || [],
                    holdings: parsed.holdings || {},
                    prices: parsed.prices || {},
                    manualSales: parsed.manualSales || []
                };
            }
        } catch (e) {
            console.error('Failed to load wheel data', e);
        }
        return { positions: [], holdings: {}, prices: {}, manualSales: [] };
    }

    function saveState() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }

    function uid() {
        return 'p_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
    }

    function todayStr() {
        return new Date().toISOString().slice(0, 10);
    }

    function daysBetween(d1, d2) {
        const ms = new Date(d2) - new Date(d1);
        return Math.max(1, Math.round(ms / 86400000));
    }

    function fmtMoney(v) {
        if (v === null || v === undefined || isNaN(v)) return '—';
        const sign = v < 0 ? '-' : '';
        return sign + 'R$ ' + Math.abs(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function fmtPct(v) {
        if (v === null || v === undefined || isNaN(v)) return '—';
        return (v * 100).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + '%';
    }

    function fmtDate(d) {
        if (!d) return '—';
        const [y, m, day] = d.split('-');
        return `${day}/${m}/${y}`;
    }

    // ---- Domain calculations ----

    function netPremium(p) {
        const gross = p.premium * 100 * p.contracts;
        const paidToClose = p.buybackPrice ? p.buybackPrice * 100 * p.contracts : 0;
        return gross - paidToClose;
    }

    function annualizedReturn(p) {
        if (!p.strike) return null;
        const days = daysBetween(p.openDate, p.expiration);
        const returnOnRisk = p.premium / p.strike;
        return returnOnRisk * (365 / days);
    }

    function openPositions() {
        return state.positions.filter(p => p.status === 'OPEN');
    }

    function closedPositions() {
        return state.positions.filter(p => p.status !== 'OPEN');
    }

    function allTickers() {
        const set = new Set();
        state.positions.forEach(p => set.add(p.ticker));
        Object.keys(state.holdings).forEach(t => set.add(t));
        return Array.from(set).sort();
    }

    function tickerSummary(ticker) {
        const positions = state.positions.filter(p => p.ticker === ticker);
        const totalPremium = positions.reduce((sum, p) => sum + netPremium(p), 0);
        const holding = state.holdings[ticker] || { shares: 0, costBasis: 0 };
        const openPut = positions.find(p => p.status === 'OPEN' && p.type === 'PUT');
        const openCall = positions.find(p => p.status === 'OPEN' && p.type === 'CALL');

        let phase;
        let nextExpiration = null;
        if (openCall) {
            phase = 'Call coberta vendida';
            nextExpiration = openCall.expiration;
        } else if (holding.shares > 0) {
            phase = 'Aguardando venda de Call coberta';
        } else if (openPut) {
            phase = 'Put vendida, aguardando vencimento';
            nextExpiration = openPut.expiration;
        } else {
            phase = 'Sem posição ativa';
        }

        return {
            ticker,
            phase,
            shares: holding.shares,
            costBasis: holding.costBasis,
            avgCost: holding.shares > 0 ? holding.costBasis / holding.shares : null,
            totalPremium,
            nextExpiration
        };
    }

    // ---- State mutations ----

    function addPosition(data) {
        state.positions.push({
            id: uid(),
            ticker: data.ticker.toUpperCase().trim(),
            type: data.type,
            strike: data.strike,
            premium: data.premium,
            contracts: data.contracts,
            openDate: data.openDate,
            expiration: data.expiration,
            notes: data.notes || '',
            status: 'OPEN'
        });
        saveState();
    }

    function deletePosition(id) {
        const p = state.positions.find(x => x.id === id);
        if (!p) return;
        if (p.status !== 'OPEN') return;
        state.positions = state.positions.filter(x => x.id !== id);
        saveState();
    }

    function resolvePosition(id, outcome, extra) {
        const p = state.positions.find(x => x.id === id);
        if (!p || p.status !== 'OPEN') return;
        extra = extra || {};
        p.closeDate = extra.closeDate || todayStr();

        if (outcome === 'BUYBACK') {
            p.buybackPrice = extra.buybackPrice;
            p.status = 'RECOMPRADA';
        } else if (outcome === 'EXPIRED') {
            p.status = 'EXPIRED';
        } else if (outcome === 'ASSIGNED' && p.type === 'PUT') {
            const sharesAdded = p.contracts * 100;
            const netCost = (p.strike * sharesAdded) - (p.premium * sharesAdded);
            const h = state.holdings[p.ticker] || { shares: 0, costBasis: 0 };
            h.shares += sharesAdded;
            h.costBasis += netCost;
            state.holdings[p.ticker] = h;
            p.status = 'ASSIGNED';
        } else if (outcome === 'CALLED_AWAY' && p.type === 'CALL') {
            const sharesRemoved = p.contracts * 100;
            const h = state.holdings[p.ticker] || { shares: 0, costBasis: 0 };
            if (h.shares > 0) {
                const removed = Math.min(sharesRemoved, h.shares);
                const ratio = removed / h.shares;
                const costRemoved = h.costBasis * ratio;
                const proceeds = p.strike * removed;
                p.capitalGain = proceeds - costRemoved;
                h.shares -= removed;
                h.costBasis -= costRemoved;
                if (h.shares <= 0.0001) { h.shares = 0; h.costBasis = 0; }
            } else {
                p.capitalGain = 0;
            }
            state.holdings[p.ticker] = h;
            p.status = 'CALLED_AWAY';
        }
        saveState();
    }

    function manualSell(ticker, shares, price) {
        const h = state.holdings[ticker];
        if (!h || h.shares <= 0) return;
        const removed = Math.min(shares, h.shares);
        const ratio = removed / h.shares;
        const costRemoved = h.costBasis * ratio;
        const proceeds = price * removed;
        const gain = proceeds - costRemoved;
        h.shares -= removed;
        h.costBasis -= costRemoved;
        if (h.shares <= 0.0001) { h.shares = 0; h.costBasis = 0; }
        state.manualSales.push({ id: uid(), ticker, shares: removed, price, gain, date: todayStr() });
        saveState();
    }

    function setPrice(ticker, price) {
        state.prices[ticker] = price;
        saveState();
    }

    // ---- Rendering ----

    function render() {
        renderDashboard();
        renderOpenPositions();
        renderHoldings();
        renderHistory();
    }

    function renderDashboard() {
        const positions = state.positions;
        const totalPremium = positions.reduce((s, p) => s + netPremium(p), 0);
        const capitalAtRisk = openPositions()
            .filter(p => p.type === 'PUT')
            .reduce((s, p) => s + p.strike * 100 * p.contracts, 0);
        const activeCycles = allTickers().filter(t => {
            const h = state.holdings[t];
            const hasOpen = state.positions.some(p => p.ticker === t && p.status === 'OPEN');
            return hasOpen || (h && h.shares > 0);
        }).length;
        const returns = positions.map(annualizedReturn).filter(r => r !== null && isFinite(r));
        const avgReturn = returns.length ? returns.reduce((a, b) => a + b, 0) / returns.length : null;

        const cards = [
            { label: 'Prêmio Total Coletado', value: fmtMoney(totalPremium), cls: totalPremium >= 0 ? 'positive' : 'negative' },
            { label: 'Capital em Risco (Puts)', value: fmtMoney(capitalAtRisk), cls: '' },
            { label: 'Ciclos Ativos', value: String(activeCycles), cls: '' },
            { label: 'Retorno Médio Anualizado', value: avgReturn !== null ? fmtPct(avgReturn) : '—', cls: '' }
        ];
        document.getElementById('summary-cards').innerHTML = cards.map(c => `
            <div class="card">
                <div class="label">${c.label}</div>
                <div class="value ${c.cls}">${c.value}</div>
            </div>
        `).join('');

        const tickers = allTickers();
        const tbody = document.querySelector('#ticker-summary-table tbody');
        if (!tickers.length) {
            tbody.innerHTML = `<tr class="empty-row"><td colspan="6">Nenhuma operação registrada ainda.</td></tr>`;
        } else {
            tbody.innerHTML = tickers.map(t => {
                const s = tickerSummary(t);
                return `<tr>
                    <td>${s.ticker}</td>
                    <td>${s.phase}</td>
                    <td>${s.shares}</td>
                    <td>${s.avgCost !== null ? fmtMoney(s.avgCost) : '—'}</td>
                    <td class="${s.totalPremium >= 0 ? 'positive' : 'negative'}">${fmtMoney(s.totalPremium)}</td>
                    <td>${s.nextExpiration ? fmtDate(s.nextExpiration) : '—'}</td>
                </tr>`;
            }).join('');
        }

        renderChart();
    }

    function renderChart() {
        const canvas = document.getElementById('premium-chart');
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const sorted = [...state.positions].sort((a, b) => a.openDate.localeCompare(b.openDate));
        if (!sorted.length) {
            ctx.fillStyle = getComputedStyle(document.body).getPropertyValue('--muted') || '#888';
            ctx.font = '14px sans-serif';
            ctx.fillText('Sem dados suficientes para exibir o gráfico.', 16, 30);
            return;
        }

        let cumulative = 0;
        const points = sorted.map(p => {
            cumulative += netPremium(p);
            return { date: p.openDate, value: cumulative };
        });

        const padding = 40;
        const w = canvas.width - padding * 2;
        const h = canvas.height - padding * 2;
        const maxVal = Math.max(...points.map(p => p.value), 0);
        const minVal = Math.min(...points.map(p => p.value), 0);
        const range = (maxVal - minVal) || 1;

        const style = getComputedStyle(document.body);
        const accent = style.getPropertyValue('--accent') || '#0d6efd';
        const border = style.getPropertyValue('--border') || '#e1e6ea';
        const muted = style.getPropertyValue('--muted') || '#888';

        // axis
        ctx.strokeStyle = border;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, padding + h);
        ctx.lineTo(padding + w, padding + h);
        ctx.stroke();

        // zero line
        const zeroY = padding + h - ((0 - minVal) / range) * h;
        ctx.strokeStyle = muted;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padding, zeroY);
        ctx.lineTo(padding + w, zeroY);
        ctx.stroke();
        ctx.setLineDash([]);

        // line
        ctx.strokeStyle = accent;
        ctx.lineWidth = 2;
        ctx.beginPath();
        points.forEach((p, i) => {
            const x = padding + (points.length > 1 ? (i / (points.length - 1)) * w : 0);
            const y = padding + h - ((p.value - minVal) / range) * h;
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        ctx.stroke();

        // labels
        ctx.fillStyle = muted;
        ctx.font = '11px sans-serif';
        ctx.fillText(fmtMoney(maxVal), 4, padding + 4);
        ctx.fillText(fmtMoney(minVal), 4, padding + h);
        ctx.fillText(fmtDate(points[0].date), padding, padding + h + 16);
        ctx.fillText(fmtDate(points[points.length - 1].date), padding + w - 60, padding + h + 16);
    }

    function renderOpenPositions() {
        const tbody = document.querySelector('#open-positions-table tbody');
        const open = openPositions().sort((a, b) => a.expiration.localeCompare(b.expiration));
        if (!open.length) {
            tbody.innerHTML = `<tr class="empty-row"><td colspan="10">Nenhuma posição aberta.</td></tr>`;
            return;
        }
        tbody.innerHTML = open.map(p => {
            const dte = daysBetween(todayStr(), p.expiration);
            const ret = annualizedReturn(p);
            const pillClass = p.type === 'PUT' ? 'put' : 'call';
            const label = p.type === 'PUT' ? 'PUT' : 'CALL';
            return `<tr>
                <td>${p.ticker}</td>
                <td><span class="pill ${pillClass}">${label}</span></td>
                <td>${fmtMoney(p.strike)}</td>
                <td>${fmtMoney(p.premium)}</td>
                <td>${p.contracts}</td>
                <td>${fmtDate(p.openDate)}</td>
                <td>${fmtDate(p.expiration)}</td>
                <td>${dte}d</td>
                <td>${ret !== null ? fmtPct(ret) : '—'}</td>
                <td class="action-cell">
                    <button class="btn-small" data-action="expired" data-id="${p.id}">Expirou</button>
                    <button class="btn-small" data-action="${p.type === 'PUT' ? 'assigned' : 'called_away'}" data-id="${p.id}">${p.type === 'PUT' ? 'Atribuída' : 'Exercida'}</button>
                    <button class="btn-small" data-action="buyback" data-id="${p.id}">Recomprar</button>
                    <button class="btn-small" data-action="delete" data-id="${p.id}">Excluir</button>
                </td>
            </tr>`;
        }).join('');
    }

    function renderHoldings() {
        const tbody = document.querySelector('#holdings-table tbody');
        const tickers = Object.keys(state.holdings).filter(t => state.holdings[t].shares > 0).sort();
        if (!tickers.length) {
            tbody.innerHTML = `<tr class="empty-row"><td colspan="8">Nenhuma ação em carteira.</td></tr>`;
            return;
        }
        tbody.innerHTML = tickers.map(t => {
            const h = state.holdings[t];
            const avgCost = h.costBasis / h.shares;
            const price = state.prices[t];
            const marketValue = price ? price * h.shares : null;
            const unrealized = price ? marketValue - h.costBasis : null;
            return `<tr>
                <td>${t}</td>
                <td>${h.shares}</td>
                <td>${fmtMoney(h.costBasis)}</td>
                <td>${fmtMoney(avgCost)}</td>
                <td><input type="number" step="0.01" class="price-input" data-ticker="${t}" value="${price || ''}" placeholder="informar" style="width:90px"></td>
                <td>${marketValue !== null ? fmtMoney(marketValue) : '—'}</td>
                <td class="${unrealized !== null && unrealized >= 0 ? 'positive' : (unrealized !== null ? 'negative' : '')}">${unrealized !== null ? fmtMoney(unrealized) : '—'}</td>
                <td><button class="btn-small" data-action="manual-sell" data-ticker="${t}">Vender</button></td>
            </tr>`;
        }).join('');
    }

    function renderHistory() {
        const tbody = document.querySelector('#history-table tbody');
        const closed = closedPositions().sort((a, b) => (b.closeDate || '').localeCompare(a.closeDate || ''));
        const manual = state.manualSales.map(m => ({ manual: true, ...m }));
        const rows = [];

        closed.forEach(p => {
            const ret = annualizedReturn(p);
            const outcomeLabels = { EXPIRED: 'Expirou', ASSIGNED: 'Atribuída', CALLED_AWAY: 'Exercida', RECOMPRADA: 'Recomprada' };
            rows.push({
                ticker: p.ticker,
                type: p.type,
                strike: p.strike,
                netPrem: netPremium(p),
                outcome: outcomeLabels[p.status] || p.status,
                closeDate: p.closeDate,
                capitalGain: p.capitalGain,
                ret
            });
        });

        manual.forEach(m => {
            rows.push({
                ticker: m.ticker,
                type: 'AÇÕES',
                strike: m.price,
                netPrem: 0,
                outcome: 'Venda Manual',
                closeDate: m.date,
                capitalGain: m.gain,
                ret: null
            });
        });

        rows.sort((a, b) => (b.closeDate || '').localeCompare(a.closeDate || ''));

        if (!rows.length) {
            tbody.innerHTML = `<tr class="empty-row"><td colspan="8">Nenhum histórico ainda.</td></tr>`;
            return;
        }

        tbody.innerHTML = rows.map(r => `
            <tr>
                <td>${r.ticker}</td>
                <td>${r.type}</td>
                <td>${fmtMoney(r.strike)}</td>
                <td class="${r.netPrem >= 0 ? 'positive' : 'negative'}">${fmtMoney(r.netPrem)}</td>
                <td>${r.outcome}</td>
                <td>${fmtDate(r.closeDate)}</td>
                <td class="${r.capitalGain === undefined || r.capitalGain === null ? '' : (r.capitalGain >= 0 ? 'positive' : 'negative')}">${r.capitalGain === undefined || r.capitalGain === null ? '—' : fmtMoney(r.capitalGain)}</td>
                <td>${r.ret !== null && r.ret !== undefined ? fmtPct(r.ret) : '—'}</td>
            </tr>
        `).join('');
    }

    // ---- Modal ----

    function openModal(html, onSubmit) {
        const overlay = document.getElementById('modal-overlay');
        const box = document.getElementById('modal-box');
        box.innerHTML = html;
        overlay.classList.remove('hidden');
        const form = box.querySelector('form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const data = {};
            form.querySelectorAll('[name]').forEach(el => { data[el.name] = el.value; });
            closeModal();
            onSubmit(data);
        });
        box.querySelector('[data-cancel]').addEventListener('click', closeModal);
    }

    function closeModal() {
        document.getElementById('modal-overlay').classList.add('hidden');
        document.getElementById('modal-box').innerHTML = '';
    }

    // ---- Event wiring ----

    function wireTabs() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
            });
        });
    }

    function wireForm() {
        const form = document.getElementById('new-position-form');
        const feedback = document.getElementById('new-position-feedback');
        document.getElementById('f-open-date').value = todayStr();

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const ticker = document.getElementById('f-ticker').value.trim();
            const type = document.getElementById('f-type').value;
            const strike = parseFloat(document.getElementById('f-strike').value);
            const premium = parseFloat(document.getElementById('f-premium').value);
            const contracts = parseInt(document.getElementById('f-contracts').value, 10);
            const openDate = document.getElementById('f-open-date').value;
            const expiration = document.getElementById('f-expiration').value;
            const notes = document.getElementById('f-notes').value;

            if (!ticker || !strike || !premium || !contracts || !openDate || !expiration) {
                feedback.textContent = 'Preencha todos os campos obrigatórios.';
                feedback.classList.add('error');
                return;
            }
            if (expiration < openDate) {
                feedback.textContent = 'A data de vencimento deve ser posterior à data de abertura.';
                feedback.classList.add('error');
                return;
            }
            if (type === 'CALL') {
                const h = state.holdings[ticker.toUpperCase().trim()];
                const shares = h ? h.shares : 0;
                if (shares < contracts * 100) {
                    feedback.textContent = `Aviso: você registrou uma Call coberta para ${contracts * 100} ações, mas possui apenas ${shares} em carteira.`;
                    feedback.classList.remove('error');
                } else {
                    feedback.textContent = 'Operação registrada com sucesso.';
                    feedback.classList.remove('error');
                }
            } else {
                feedback.textContent = 'Operação registrada com sucesso.';
                feedback.classList.remove('error');
            }

            addPosition({ ticker, type, strike, premium, contracts, openDate, expiration, notes });
            form.reset();
            document.getElementById('f-open-date').value = todayStr();
            render();
        });
    }

    function wireTableActions() {
        document.querySelector('#open-positions-table tbody').addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-action]');
            if (!btn) return;
            const id = btn.dataset.id;
            const action = btn.dataset.action;

            if (action === 'expired') {
                resolvePosition(id, 'EXPIRED');
                render();
            } else if (action === 'assigned') {
                resolvePosition(id, 'ASSIGNED');
                render();
            } else if (action === 'called_away') {
                resolvePosition(id, 'CALLED_AWAY');
                render();
            } else if (action === 'delete') {
                if (confirm('Excluir esta posição aberta? Esta ação não pode ser desfeita.')) {
                    deletePosition(id);
                    render();
                }
            } else if (action === 'buyback') {
                openModal(`
                    <h3>Recomprar Opção</h3>
                    <form>
                        <label>Preço pago por ação para fechar
                            <input type="number" name="buybackPrice" step="0.01" min="0" required autofocus>
                        </label>
                        <label>Data de fechamento
                            <input type="date" name="closeDate" value="${todayStr()}" required>
                        </label>
                        <div class="modal-actions">
                            <button type="button" class="btn-secondary" data-cancel>Cancelar</button>
                            <button type="submit" class="btn-primary">Confirmar</button>
                        </div>
                    </form>
                `, (data) => {
                    resolvePosition(id, 'BUYBACK', { buybackPrice: parseFloat(data.buybackPrice), closeDate: data.closeDate });
                    render();
                });
            }
        });

        document.querySelector('#holdings-table tbody').addEventListener('click', (e) => {
            const btn = e.target.closest('button[data-action="manual-sell"]');
            if (!btn) return;
            const ticker = btn.dataset.ticker;
            const h = state.holdings[ticker];
            openModal(`
                <h3>Vender Ações Manualmente - ${ticker}</h3>
                <form>
                    <label>Quantidade de ações (disponível: ${h.shares})
                        <input type="number" name="shares" min="1" max="${h.shares}" value="${h.shares}" required autofocus>
                    </label>
                    <label>Preço de venda por ação
                        <input type="number" name="price" step="0.01" min="0" required>
                    </label>
                    <div class="modal-actions">
                        <button type="button" class="btn-secondary" data-cancel>Cancelar</button>
                        <button type="submit" class="btn-primary">Confirmar Venda</button>
                    </div>
                </form>
            `, (data) => {
                manualSell(ticker, parseInt(data.shares, 10), parseFloat(data.price));
                render();
            });
        });

        document.querySelector('#holdings-table tbody').addEventListener('change', (e) => {
            const input = e.target.closest('.price-input');
            if (!input) return;
            const val = parseFloat(input.value);
            if (!isNaN(val)) {
                setPrice(input.dataset.ticker, val);
                render();
            }
        });
    }

    function wireFooter() {
        document.getElementById('btn-export').addEventListener('click', () => {
            const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `wheel-strategy-${todayStr()}.json`;
            a.click();
            URL.revokeObjectURL(url);
        });

        document.getElementById('btn-import').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = () => {
                try {
                    const parsed = JSON.parse(reader.result);
                    state = {
                        positions: parsed.positions || [],
                        holdings: parsed.holdings || {},
                        prices: parsed.prices || {},
                        manualSales: parsed.manualSales || []
                    };
                    saveState();
                    render();
                } catch (err) {
                    alert('Arquivo inválido.');
                }
            };
            reader.readAsText(file);
            e.target.value = '';
        });

        document.getElementById('btn-reset').addEventListener('click', () => {
            if (confirm('Isso apagará todos os dados salvos localmente. Deseja continuar?')) {
                state = { positions: [], holdings: {}, prices: {}, manualSales: [] };
                saveState();
                render();
            }
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        wireTabs();
        wireForm();
        wireTableActions();
        wireFooter();
        render();
    });
})();
