"""Cloud Functions for the AI-powered asset analyzer.

Fetches market data via yfinance and uses the Anthropic API to produce
Portuguese-language summaries: recent news, technical trend, and
fundamental trend for a given ticker.
"""

import json
import re

import anthropic
import yfinance as yf
from firebase_functions import https_fn, options
from firebase_functions.params import SecretParam

ANTHROPIC_API_KEY = SecretParam("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-5"

TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,14}$")

FUNCTION_OPTS = dict(
    secrets=[ANTHROPIC_API_KEY],
    memory=options.MemoryOption.MB_512,
    timeout_sec=120,
    region="us-central1",
)


def _require_auth(req: https_fn.CallableRequest) -> None:
    if req.auth is None:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAUTHENTICATED,
            message="É necessário estar autenticado para usar a análise por IA.",
        )


def _clean_ticker(raw) -> str:
    ticker = str(raw or "").strip().upper()
    if not ticker or not TICKER_RE.match(ticker):
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
            message="Código de ativo inválido.",
        )
    return ticker


def _ask_claude(system: str, user: str) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY.value)
    message = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(block.text for block in message.content if block.type == "text")
    match = re.search(r"\{.*\}", text, re.DOTALL)
    try:
        return json.loads(match.group(0)) if match else {"raw": text}
    except json.JSONDecodeError:
        return {"raw": text}


@https_fn.on_call(**FUNCTION_OPTS)
def get_asset_news(req: https_fn.CallableRequest) -> dict:
    _require_auth(req)
    ticker = _clean_ticker(req.data.get("ticker"))

    try:
        raw_news = yf.Ticker(ticker).news or []
    except Exception as exc:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAVAILABLE,
            message=f"Não foi possível buscar notícias para {ticker}.",
        ) from exc

    headlines = []
    for item in raw_news[:20]:
        content = item.get("content", item)
        title = content.get("title")
        if not title:
            continue
        summary = content.get("summary") or content.get("description") or ""
        url = (content.get("canonicalUrl") or {}).get("url") or content.get("link") or ""
        publisher = (content.get("provider") or {}).get("displayName") or content.get("publisher") or ""
        pub_date = content.get("pubDate") or content.get("displayTime") or ""
        headlines.append(
            {"title": title, "summary": summary, "url": url, "publisher": publisher, "date": pub_date}
        )

    if not headlines:
        return {"ticker": ticker, "items": [], "message": "Nenhuma notícia recente encontrada."}

    system = (
        "Você é um analista financeiro. Receberá uma lista de manchetes de notícias recentes "
        "sobre uma empresa/ativo. Selecione até 5 notícias realmente relevantes para um investidor "
        "e responda SOMENTE com um JSON no formato: "
        '{"items": [{"title": str, "summary": str (1-2 frases em português explicando a relevância '
        'e o possível impacto no preço), "impact": "positivo"|"negativo"|"neutro", "url": str}]}. '
        "Não inclua nenhum texto fora do JSON."
    )
    user = f"Ativo: {ticker}\n\nManchetes:\n" + json.dumps(headlines, ensure_ascii=False, indent=2)

    result = _ask_claude(system, user)
    result["ticker"] = ticker
    return result


@https_fn.on_call(**FUNCTION_OPTS)
def get_technical_analysis(req: https_fn.CallableRequest) -> dict:
    _require_auth(req)
    ticker = _clean_ticker(req.data.get("ticker"))

    try:
        hist = yf.Ticker(ticker).history(period="1y", interval="1d")
    except Exception as exc:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAVAILABLE,
            message=f"Não foi possível buscar o histórico de preços para {ticker}.",
        ) from exc

    if hist.empty or len(hist) < 20:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message=f"Histórico de preços insuficiente para {ticker}.",
        )

    close = hist["Close"]
    last = float(close.iloc[-1])

    def pct_change(days):
        if len(close) <= days:
            return None
        return round(((last / float(close.iloc[-days - 1])) - 1) * 100, 2)

    def sma(window):
        if len(close) < window:
            return None
        return round(float(close.tail(window).mean()), 4)

    metrics = {
        "preco_atual": round(last, 4),
        "variacao_1m_pct": pct_change(21),
        "variacao_3m_pct": pct_change(63),
        "variacao_6m_pct": pct_change(126),
        "variacao_12m_pct": pct_change(min(251, len(close) - 1)),
        "media_movel_20": sma(20),
        "media_movel_50": sma(50),
        "media_movel_200": sma(200),
        "maxima_52_semanas": round(float(close.max()), 4),
        "minima_52_semanas": round(float(close.min()), 4),
    }

    system = (
        "Você é um analista técnico. Receberá métricas de preço de um ativo (médias móveis, "
        "variações percentuais, máximas e mínimas de 52 semanas). Classifique a tendência atual "
        "e responda SOMENTE com um JSON no formato: "
        '{"classificacao": "alta"|"baixa"|"lateral", "confianca": "alta"|"média"|"baixa", '
        '"resumo": str (3-4 frases em português explicando o racional com base nas médias móveis '
        'e variações fornecidas)}. Não inclua nenhum texto fora do JSON.'
    )
    user = f"Ativo: {ticker}\n\nMétricas:\n" + json.dumps(metrics, ensure_ascii=False, indent=2)

    result = _ask_claude(system, user)
    result["ticker"] = ticker
    result["metricas"] = metrics
    return result


@https_fn.on_call(**FUNCTION_OPTS)
def get_fundamental_analysis(req: https_fn.CallableRequest) -> dict:
    _require_auth(req)
    ticker = _clean_ticker(req.data.get("ticker"))

    asset = yf.Ticker(ticker)
    try:
        info = asset.info or {}
    except Exception as exc:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.UNAVAILABLE,
            message=f"Não foi possível buscar dados fundamentalistas para {ticker}.",
        ) from exc

    fields = [
        "quoteType", "sector", "industry", "revenueGrowth", "earningsGrowth",
        "earningsQuarterlyGrowth", "grossMargins", "operatingMargins", "profitMargins",
        "returnOnEquity", "returnOnAssets", "debtToEquity", "currentRatio",
        "trailingPE", "forwardPE", "pegRatio", "freeCashflow", "totalRevenue",
        "netIncomeToCommon",
    ]
    fundamentals = {f: info.get(f) for f in fields if info.get(f) is not None}

    try:
        financials = asset.financials
        if financials is not None and not financials.empty:
            if "Total Revenue" in financials.index:
                fundamentals["receita_anual_recente_primeiro"] = [
                    round(float(v), 2) for v in financials.loc["Total Revenue"].dropna().tolist()[:4]
                ]
            if "Net Income" in financials.index:
                fundamentals["lucro_liquido_anual_recente_primeiro"] = [
                    round(float(v), 2) for v in financials.loc["Net Income"].dropna().tolist()[:4]
                ]
    except Exception:
        pass

    if not fundamentals:
        raise https_fn.HttpsError(
            code=https_fn.FunctionsErrorCode.NOT_FOUND,
            message=f"Dados fundamentalistas insuficientes para {ticker}.",
        )

    system = (
        "Você é um analista fundamentalista. Receberá indicadores financeiros de uma empresa "
        "(alguns campos podem faltar, especialmente para ETFs/fundos). Avalie se a empresa está "
        "crescendo, estável ou diminuindo. Responda SOMENTE com um JSON no formato: "
        '{"classificacao": "crescendo"|"estável"|"diminuindo"|"dados insuficientes", '
        '"confianca": "alta"|"média"|"baixa", "resumo": str (3-5 frases em português explicando '
        'o racional com base nos indicadores fornecidos)}. Não inclua nenhum texto fora do JSON.'
    )
    user = f"Ativo: {ticker}\n\nIndicadores:\n" + json.dumps(fundamentals, ensure_ascii=False, indent=2, default=str)

    result = _ask_claude(system, user)
    result["ticker"] = ticker
    result["indicadores"] = fundamentals
    return result
