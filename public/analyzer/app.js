import {
    watchAuth, signInGoogle, signUpEmail, signInEmail, signOutUser,
    fetchAssetNews, fetchTechnicalAnalysis, fetchFundamentalAnalysis
} from './firebase-init.js';

(function () {
    'use strict';

    const ASSET_TYPES = {
        br_acao: { label: 'Ação Brasileira', yahooSuffix: '.SA', tvExchange: 'BMFBOVESPA' },
        br_fii: { label: 'FII', yahooSuffix: '.SA', tvExchange: 'BMFBOVESPA' },
        br_etf: { label: 'ETF Brasileiro', yahooSuffix: '.SA', tvExchange: 'BMFBOVESPA' },
        us_acao: { label: 'Ação Americana', yahooSuffix: '', tvExchange: '' },
        us_etf: { label: 'ETF Americano', yahooSuffix: '', tvExchange: '' }
    };

    /** @type {{yahooTicker: string, tvSymbol: string} | null} */
    let currentAsset = null;

    function buildAsset(rawInput, typeKey) {
        const type = ASSET_TYPES[typeKey] || ASSET_TYPES.br_acao;
        let base = rawInput.trim().toUpperCase();
        let explicitExchange = null;

        if (base.includes(':')) {
            const [exchange, symbol] = base.split(':');
            explicitExchange = exchange;
            base = symbol;
        }
        base = base.replace(/\.SA$/, '');

        const yahooTicker = base + type.yahooSuffix;
        const tvExchange = explicitExchange || type.tvExchange;
        const tvSymbol = tvExchange ? `${tvExchange}:${base}` : base;

        return { yahooTicker, tvSymbol };
    }

    function loadTradingViewWidget(containerId, scriptSrc, config) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        const inner = document.createElement('div');
        inner.className = 'tradingview-widget-container__widget';
        container.appendChild(inner);

        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = scriptSrc;
        script.async = true;
        script.text = JSON.stringify(config);
        container.appendChild(script);
    }

    function renderWidgets(asset) {
        loadTradingViewWidget('tv-chart', 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js', {
            autosize: true,
            symbol: asset.tvSymbol,
            interval: 'D',
            timezone: 'America/Sao_Paulo',
            theme: 'dark',
            style: '1',
            locale: 'br',
            withdateranges: true,
            allow_symbol_change: true,
            support_host: 'https://www.tradingview.com'
        });

        loadTradingViewWidget('tv-symbol-info', 'https://s3.tradingview.com/external-embedding/embed-widget-symbol-info.js', {
            symbol: asset.tvSymbol,
            colorTheme: 'dark',
            isTransparent: false,
            locale: 'br'
        });

        loadTradingViewWidget('tv-financials', 'https://s3.tradingview.com/external-embedding/embed-widget-financials.js', {
            symbol: asset.tvSymbol,
            colorTheme: 'dark',
            isTransparent: false,
            displayMode: 'regular',
            locale: 'br'
        });

        document.getElementById('widgets-section').classList.remove('hidden');
        document.getElementById('ai-section').classList.remove('hidden');
    }

    function resetAiPanels() {
        document.getElementById('panel-news').innerHTML =
            '<div class="ai-panel-empty">Clique em "Principais Notícias" para buscar as notícias mais relevantes sobre o ativo.</div>';
        document.getElementById('panel-technical').innerHTML =
            '<div class="ai-panel-empty">Clique em "Tendência Gráfica" para uma avaliação técnica de alta, baixa ou lateralização.</div>';
        document.getElementById('panel-fundamental').innerHTML =
            '<div class="ai-panel-empty">Clique em "Avaliação Fundamentalista" para saber se a empresa está crescendo, estável ou diminuindo.</div>';
    }

    function setLoading(panelId, message) {
        document.getElementById(panelId).innerHTML = `<div class="ai-panel-loading">${message}</div>`;
    }

    function setError(panelId, message) {
        document.getElementById(panelId).innerHTML = `<div class="ai-panel-error">${escapeHtml(message)}</div>`;
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = String(str == null ? '' : str);
        return div.innerHTML;
    }

    function trendPillClass(classification) {
        const c = (classification || '').toLowerCase();
        if (['alta', 'crescendo'].includes(c)) return 'up';
        if (['baixa', 'diminuindo'].includes(c)) return 'down';
        if (['lateral', 'estável', 'estavel'].includes(c)) return 'flat';
        return 'unknown';
    }

    function renderNews(panelId, data) {
        const panel = document.getElementById(panelId);
        if (data.raw) {
            panel.innerHTML = `<p class="ai-panel-summary">${escapeHtml(data.raw)}</p>`;
            return;
        }
        const items = data.items || [];
        if (!items.length) {
            panel.innerHTML = `<div class="ai-panel-empty">${escapeHtml(data.message || 'Nenhuma notícia relevante encontrada.')}</div>`;
            return;
        }
        panel.innerHTML = `<div class="news-list">${items.map(item => `
            <div class="news-item">
                <div class="news-item-title">
                    ${item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a>` : escapeHtml(item.title)}
                    ${item.impact ? `<span class="impact-pill ${escapeHtml(item.impact.toLowerCase())}">${escapeHtml(item.impact)}</span>` : ''}
                </div>
                <div class="news-item-summary">${escapeHtml(item.summary)}</div>
            </div>
        `).join('')}</div>`;
    }

    function renderClassification(panelId, data, metricsObj) {
        const panel = document.getElementById(panelId);
        if (data.raw) {
            panel.innerHTML = `<p class="ai-panel-summary">${escapeHtml(data.raw)}</p>`;
            return;
        }
        const pillClass = trendPillClass(data.classificacao);
        let metricsHtml = '';
        if (metricsObj) {
            metricsHtml = `<div class="metrics-grid">${Object.entries(metricsObj).map(([k, v]) => `
                <div class="metric">
                    <div class="k">${escapeHtml(k.replace(/_/g, ' '))}</div>
                    <div class="v">${v === null || v === undefined ? '—' : escapeHtml(v)}</div>
                </div>
            `).join('')}</div>`;
        }
        panel.innerHTML = `
            <div class="classification-row">
                <span class="classification-pill ${pillClass}">${escapeHtml(data.classificacao || 'indefinido')}</span>
                ${data.confianca ? `<span class="classification-confidence">Confiança: ${escapeHtml(data.confianca)}</span>` : ''}
            </div>
            <p class="ai-panel-summary">${escapeHtml(data.resumo || '')}</p>
            ${metricsHtml}
        `;
    }

    async function handleAiClick(button, panelId, loadingMessage, fetchFn, renderFn) {
        if (!currentAsset) return;
        button.disabled = true;
        setLoading(panelId, loadingMessage);
        try {
            const data = await fetchFn(currentAsset.yahooTicker);
            renderFn(data);
        } catch (err) {
            console.error(err);
            setError(panelId, err && err.message ? err.message : 'Ocorreu um erro ao consultar a IA.');
        } finally {
            button.disabled = false;
        }
    }

    function wireSearchForm() {
        const form = document.getElementById('search-form');
        const feedback = document.getElementById('search-feedback');

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const raw = document.getElementById('f-ticker').value;
            const typeKey = document.getElementById('f-type').value;

            if (!raw.trim()) {
                feedback.textContent = 'Informe o código do ativo.';
                return;
            }

            feedback.textContent = '';
            currentAsset = buildAsset(raw, typeKey);
            resetAiPanels();
            renderWidgets(currentAsset);
        });
    }

    function wireAiButtons() {
        document.getElementById('btn-ai-news').addEventListener('click', (e) => {
            handleAiClick(e.currentTarget, 'panel-news', 'Buscando as principais notícias...',
                fetchAssetNews, (data) => renderNews('panel-news', data));
        });

        document.getElementById('btn-ai-technical').addEventListener('click', (e) => {
            handleAiClick(e.currentTarget, 'panel-technical', 'Avaliando a tendência gráfica...',
                fetchTechnicalAnalysis, (data) => renderClassification('panel-technical', data, data.metricas));
        });

        document.getElementById('btn-ai-fundamental').addEventListener('click', (e) => {
            handleAiClick(e.currentTarget, 'panel-fundamental', 'Avaliando os fundamentos da empresa...',
                fetchFundamentalAnalysis, (data) => renderClassification('panel-fundamental', data, data.indicadores));
        });
    }

    function showAuthError(err) {
        const feedback = document.getElementById('auth-feedback');
        feedback.textContent = describeAuthError(err);
    }

    function describeAuthError(err) {
        const code = err && err.code;
        const messages = {
            'auth/invalid-email': 'E-mail inválido.',
            'auth/user-not-found': 'Usuário não encontrado.',
            'auth/wrong-password': 'Senha incorreta.',
            'auth/invalid-credential': 'E-mail ou senha incorretos.',
            'auth/email-already-in-use': 'Este e-mail já está cadastrado.',
            'auth/weak-password': 'A senha deve ter pelo menos 6 caracteres.',
            'auth/popup-closed-by-user': 'Login com Google cancelado.'
        };
        return messages[code] || 'Não foi possível autenticar. Tente novamente.';
    }

    function wireAuth() {
        document.getElementById('btn-google-signin').addEventListener('click', () => {
            signInGoogle().catch(showAuthError);
        });

        document.getElementById('auth-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const email = document.getElementById('auth-email').value.trim();
            const password = document.getElementById('auth-password').value;
            const mode = e.submitter ? e.submitter.dataset.mode : 'signin';
            const action = mode === 'signup' ? signUpEmail(email, password) : signInEmail(email, password);
            action.catch(showAuthError);
        });

        document.getElementById('btn-signout').addEventListener('click', () => {
            signOutUser();
        });

        watchAuth((user) => {
            if (!user) {
                document.getElementById('app-shell').classList.add('hidden');
                document.getElementById('auth-screen').classList.remove('hidden');
                return;
            }
            document.getElementById('auth-screen').classList.add('hidden');
            document.getElementById('app-shell').classList.remove('hidden');
            document.getElementById('user-email').textContent = user.email || '';
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        wireSearchForm();
        wireAiButtons();
        wireAuth();
    });
})();
