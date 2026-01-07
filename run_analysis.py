import yfinance as yf
import pandas as pd
import json
import os
import sys

def run_analysis():
    """Fetches stock and ETF data and saves it as a JavaScript file."""

    brazilian_tickers = [
        "PETR4.SA", "ITUB4.SA", "BBDC4.SA", "WEGE3.SA",
        "B3SA3.SA", "SUZB3.SA", "ITSA4.SA", "GGBR4.SA", "MGLU3.SA", "RDOR3.SA",
        "JBSS3.SA", "BPAC11.SA", "LREN3.SA", "RADL3.SA", "NTCO3.SA", "BBAS3.SA",
        "CSAN3.SA", "CCRO3.SA", "RAIL3.SA", "EQTL3.SA", "ELET3.SA", "VIVT3.SA",
        "HYPE3.SA", "IRBR3.SA", "SBSP3.SA", "RENT3.SA", "CIEL3.SA", "EMBR3.SA"
    ]
    
    american_tickers = [
        "NVDA", "GOOGL", "AAPL", "GOOG", "MSFT", "AMZN", "META", "AVGO", "TSLA",
        "BRK.B", "BRK.A", "LLY", "WMT", "JPM", "V", "ORCL", "MA", "XOM", "JNJ", "ASML",
        "PLTR", "NFLX", "ABBV", "BAC", "COST", "MU", "HD", "GE", "AMD", "PG",
        "CVX", "UNH", "GS", "CSCO", "WFC", "MS", "AZN", "KO", "HSBC", "CAT", "IBM",
        "SAP", "MRK", "NVS", "AXP", "LRCX", "NVO", "RTX", "CRM", "PM", "RY", "TMO",
        "AMAT", "ABT", "TMUS", "SHOP", "C", "MCD", "APP", "INTC", "ISRG", "SHEL", "LIN",
        "DIS", "BX", "QCOM", "PEP", "MUFG", "AMGN", "SCHW", "GEV", "INTU", "UBER",
        "KLAC", "BLK", "BKNG", "BA", "SAN", "TJX", "APH", "T", "VZ", "TXN", "ACN",
        "DHR", "ANET", "NEE", "SPGI", "BHP", "COF", "TD", "NOW", "GILD",
        "UBS", "BSX", "RIO", "ADI", "PFE", "ADBE", "SYK", "LOW", "TTE", "PANW", "UL",
        "UNP", "BBVA", "DE", "SCCO", "WELL", "MDT", "SMFG", "HON", "ETN", "BUD", "PGR",
        "ARM", "VRTX", "CRWD", "PLD", "CB", "KKR", "SPOT", "NEM", "LMT", "SNY",
        "BTI", "PH", "BMY", "BN", "MELI", "HCA", "HOOD", "ADP", "CEG", "GSK",
        "MCK", "CVS", "CMCSA", "SNPS", "ENB", "DASH", "CVNA", "SBUX", "CME", "MFG",
        "SO", "MCO", "GD", "BMO", "NKE", "ICE", "MO", "AEM", "DUK", "MMC", "UPS",
        "BNS", "BP", "BAM", "BCS", "CDNS", "WM", "MMM", "MAR", "HWM", "USB", "NU", "APO",
        "PNC", "NOC", "CM", "BK", "TT", "ING", "ABNB", "SE", "REGN", "CRH", "RCL", "SHW",
        "ELV", "B", "EMR", "SNOW", "AMT", "DELL", "ITUB", "FCX", "NGG", "LYG", "TDG",
        "ORLY", "RELX", "EQIX", "GM", "ECL", "GLW", "AON", "CTAS", "CI", "CMI", "DB",
        "MNST", "WMB", "INFY", "PBR.A", "FDX", "ITW", "MRVL", "NWG", "NET",
        "WBD", "SPG", "JCI", "WDC", "HLT", "EPD", "TEL", "STX", "MDLZ", "AJG", "VRT",
        "CP", "COR", "COIN", "CNQ", "PWR", "RACE", "CSX", "RSG", "TFC", "NSC", "SLB",
        "TRV", "MSI", "MFC", "CL", "ADSK", "CNI", "PCAR", "AEP", "ROST", "KMI",
        "NXPI", "RKT", "EQNR", "FTNT", "TRI", "LHX", "E", "APD", "AFL", "BDX",
        "NDAQ", "IDXX", "WPM", "SRE", "VLO", "ARES", "EOG", "URI", "ALNY", "ZTS",
        "WDAY", "PSX", "AZO", "PYPL", "SU", "DLR", "F", "ALL", "TRP", "RBLX", "MPLX", "O",
        "VST", "MET", "MPC", "CMG", "EA", "CBRE", "CAH",
        "AXON", "RDDT", "ARGX", "AME", "HEI", "MSTR", "EW", "D", "BKR", "GWW", "FER",
        "TTWO", "DEO", "PSA", "TGT", "ROP", "DAL", "AU", "FAST", "AMP", "CTVA", "ROK",
        "MPWR", "RKLB", "OKE", "HLN", "CARR", "CCJ", "MSCI", "FERG", "IMO", "EXC",
        "WCN", "XEL", "TEAM", "CPNG", "CUK", "FNV", "SYM", "CCL", "AIG", "HEI.A",
        "A", "YUM", "LVS", "IQV", "ETR", "GFI", "DHI", "PUK", "PRU", "OXY", "CTSH",
        "EBAY", "GRMN", "PAYX", "ALC", "MCHP", "VEEV", "TKO", "GEHC",
        "PEG", "VMC", "CCEP", "HMC", "TRGP", "EL", "HIG", "MLM", "NUE",
        "FICO", "NOK", "KR", "INSM", "CCI", "WAB", "CPRT", "FISV", "TEVA", "STT", "KDP",
        "FLUT", "KGC", "ZS", "KEYS", "HSY", "RYAAY", "EXPE", "CIEN", "FIX", "RMD",
        "VTR", "MDB", "ED", "SLF", "NTRA", "MT", "CLS", "ODFL", "SYY", "BBDO",
        "FIS", "OTIS", "TER", "PCG", "UI", "ACGL", "SOFI", "WEC", "EQT", "XYL",
        "LYV", "HUM", "IX", "ERIC", "VIK", "FOXA", "COHR", "CHT", "VOD", "RJF", "KMB",
        "IR", "FITB", "MTB", "IBKR", "KVUE", "ASTS", "WTW", "FOX", "SYF",
        "DG", "WIT", "STLA", "VRSK", "QSR", "CHTR", "HPE", "MTD", "EXR",
        "VICI", "NTR", "EME", "ESLT", "WDS", "LPLA", "ULTA", "ROL", "NRG", "HBAN",
        "LITE", "ADM", "ALAB", "DXCM", "DOV", "AFRM", "KHC", "PHG", "TPR", "NTRS",
        "FCNCA", "MKL", "BIIB", "CSGP", "BRO", "CBOE", "AEE", "ATO", "DTE", "TSCO",
        "NMR", "CFG", "BE", "EFX", "DLTR", "IRM", "LEN.B", "FSLR",
        "STM", "WRB", "FTS"
    ]

    brazilian_etfs = ["BOVA11.SA", "SPXR11.SA", "LFTB11.SA", "AREA11.SA", "DIVO11.SA", "B5MB11.SA", "DOLA11.SA", "AUPO11.SA"]
    american_etfs = ["BTCI", "DIVO", "GLD", "GPIQ", "IBIT", "JEPQ", "MCHI", "QDVO", 
                     "QQQM", "SLV", "SPYI", "VIG", "VOO", "VT", "VUG"]
    etf_tickers = brazilian_etfs + american_etfs
    
    all_brazilian_assets = brazilian_tickers + brazilian_etfs

    all_tickers = brazilian_tickers + american_tickers + etf_tickers
    results = []

    print(f"--- Starting Analysis for {len(all_tickers)} Tickers (Stocks and ETFs) ---")

    for ticker in all_tickers:
        try:
            print(f"--- Processing {ticker} ---")
            asset = yf.Ticker(ticker)
            info = asset.info

            is_brazilian = ticker in all_brazilian_assets
            price_prefix = "R$" if is_brazilian else "U$"
            
            current_price = info.get('regularMarketPrice')
            formatted_current_price = f"{price_prefix} {current_price:.2f}" if current_price is not None else "N/A"

            # --- ETF Processing ---
            if ticker in etf_tickers:
                results.append({
                    'Ticker': f"{ticker} (ETF)",
                    'Preço Atual': formatted_current_price,
                    'P/FCO (O)': 'N/A',
                    'Preço Alvo': 'N/A',
                    'T (Alvo/Preço)': 'N/A',
                    'Compra Forte': 'N/A', 'Compra': 'N/A', 'Neutro': 'N/A', 'Venda': 'N/A', 'Venda Forte': 'N/A',
                    'R': 'N/A',
                    'C': 'N/A'
                })
                print(f"Successfully processed ETF: {ticker}")
                continue

            # --- Stock Processing ---
            p_fco_ratio = None
            try:
                cashflow = asset.get_cashflow()
                ocf_key = 'OperatingCashFlow'
                if not cashflow.empty and ocf_key in cashflow.index:
                    operating_cash_flow = cashflow.loc[ocf_key].iloc[0]
                    shares_outstanding = info.get('sharesOutstanding')
                    if operating_cash_flow and shares_outstanding and shares_outstanding > 0:
                        fco_per_share = operating_cash_flow / shares_outstanding
                        if current_price and fco_per_share and fco_per_share > 0:
                            p_fco_ratio = current_price / fco_per_share
            except Exception:
                pass

            target_price = info.get('targetMeanPrice')
            formatted_target_price = f"{price_prefix} {target_price:.2f}" if target_price is not None else "N/A"
            t_ratio = (target_price / current_price) if target_price and current_price and current_price > 0 else None

            recs = asset.recommendations
            strong_buy, buy, hold, sell, strong_sell = 0, 0, 0, 0, 0
            if recs is not None and not recs.empty and 'strongBuy' in recs.columns:
                latest_recs = recs.iloc[-1]
                strong_buy = int(latest_recs.get('strongBuy', 0))
                buy = int(latest_recs.get('buy', 0))
                hold = int(latest_recs.get('hold', 0))
                sell = int(latest_recs.get('sell', 0))
                strong_sell = int(latest_recs.get('strongSell', 0))

            r_value = (strong_buy * 3) + buy + (hold * -1) + (sell * -3) + (strong_sell * -5)

            c_metric = None
            if t_ratio and r_value and p_fco_ratio and p_fco_ratio != 0:
                c_metric = (t_ratio * r_value) / p_fco_ratio

            results.append({
                'Ticker': ticker,
                'Preço Atual': formatted_current_price,
                'P/FCO (O)': p_fco_ratio,
                'Preço Alvo': formatted_target_price,
                'T (Alvo/Preço)': t_ratio,
                'Compra Forte': strong_buy, 'Compra': buy, 'Neutro': hold, 'Venda': sell, 'Venda Forte': strong_sell,
                'R': r_value,
                'C': c_metric
            })
            print(f"Successfully processed Stock: {ticker}")

        except Exception as e:
            print(f'CRITICAL ERROR: Could not process {ticker}: {e}', file=sys.stderr)
            continue

    df = pd.DataFrame(results)
    json_data = df.to_json(orient='records', indent=4, default_handler=str)
    output_path = 'public/stock_data.js'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(f"const stockData = {json_data};")

    print(f"Analysis complete. Data saved to {output_path}")

if __name__ == "__main__":
    run_analysis()
