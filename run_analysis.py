import yfinance as yf
import pandas as pd
import json
import os
import sys

def run_analysis():
    """Fetches stock and ETF data and saves it as a JavaScript file."""

    brazilian_tickers = [
        "ABEV3.SA", "ALUP4.SA", "AXIA3.SA", "B3SA3.SA", "BBAS3.SA", "BBDC4.SA", 
        "BPAC11.SA", "BPAC3.SA", "BRAP3.SA", "CGRA3.SA", "CMIG3.SA", "CSAN3.SA", 
        "CSNA3.SA", "CYRE3.SA", "EQTL3.SA", "GGBR4.SA", "GOAU3.SA", "HYPE3.SA", 
        "IRBR3.SA", "ITSA4.SA", "ITUB4.SA", "KLBN3.SA", "LREN3.SA", "MDIA3.SA", 
        "MGLU3.SA", "PGMN3.SA", "PRIO3.SA", "PSSA3.SA", "RADL3.SA", "RAIL3.SA", 
        "RANI3.SA", "RDOR3.SA", "RENT3.SA", "SANB3.SA", "SAPR4.SA", "SBSP3.SA", 
        "SMFT3.SA", "SUZB3.SA", "TAEE3.SA", "TIMS3.SA", "UNIP3.SA", "USIM3.SA", 
        "VALE3.SA", "VBBR3.SA", "VIVT3.SA", "VLID3.SA", "WEGE3.SA", "YDUQ3.SA"
    ]
    
    american_tickers = [
        "NVDA", "GOOGL", "AAPL", "GOOG", "MSFT", "AMZN", "META", "AVGO", "TSLA",
        "LLY", "WMT", "V", "ORCL", "MA", "XOM", "JNJ", "ASML",
        "PLTR", "NFLX", "ABBV", "COST", "MU", "HD", "GE", "AMD", "PG",
        "CVX", "UNH", "WFC", "MS", "AZN", "KO", "HSBC", "CAT", "IBM",
        "SAP", "MRK", "NVS", "AXP", "LRCX", "NVO", "RTX", "CRM", "PM", "RY", "TMO",
        "AMAT", "ABT", "TMUS", "SHOP", "MCD", "APP", "INTC", "ISRG", "SHEL", "LIN",
        "DIS", "BX", "QCOM", "PEP", "MUFG", "AMGN", "SCHW", "GEV", "INTU", "UBER",
        "KLAC", "BLK", "BKNG", "TJX", "APH", "T", "VZ", "TXN", "ACN",
        "DHR", "ANET", "NEE", "SPGI", "BHP", "COF", "NOW", "GILD",
        "UBS", "BSX", "RIO", "ADI", "PFE", "ADBE", "SYK", "LOW", "TTE", "PANW", "UL",
        "UNP", "DE", "SCCO", "MDT", "SMFG", "HON", "ETN", "BUD", "PGR",
        "ARM", "CRWD", "CB", "KKR", "SPOT", "NEM", "LMT", "SNY",
        "BTI", "PH", "BMY", "BN", "MELI", "HCA", "GSK",
        "MCK", "CVS", "CMCSA", "SNPS", "ENB", "DASH", "CVNA", "SBUX", "CME",
        "SO", "MCO", "GD", "BMO", "NKE", "ICE", "MO", "AEM", "DUK", "MMC", "UPS",
        "BNS", "BP", "BAM", "BCS", "CDNS", "WM", "MMM", "MAR", "HWM", "USB", "NU", "APO",
        "PNC", "NOC", "CM", "BK", "TT", "ABNB", "SE", "REGN", "CRH", "RCL", "SHW",
        "ELV", "B", "EMR", "SNOW", "DELL", "ITUB", "FCX", "NGG", "TDG",
        "ORLY", "RELX", "GM", "ECL", "GLW", "AON", "CTAS", "CI", "CMI",
        "MNST", "WMB", "INFY", "FDX", "ITW", "MRVL", "NWG", "NET",
        "WBD", "JCI", "WDC", "HLT", "EPD", "TEL", "STX", "MDLZ", "AJG", "VRT",
        "CP", "COR", "COIN", "CNQ", "PWR", "RACE", "CSX", "RSG", "TFC", "NSC", "SLB",
        "TRV", "MSI", "MFC", "CL", "ADSK", "CNI", "PCAR", "AEP", "ROST", "KMI",
        "NXPI", "EQNR", "FTNT", "TRI", "LHX", "E", "APD", "AFL", "BDX",
        "NDAQ", "IDXX", "WPM", "SRE", "VLO", "ARES", "EOG", "URI", "ZTS",
        "WDAY", "PSX", "AZO", "PYPL", "SU", "F", "ALL", "TRP", "RBLX", "MPLX",
        "VST", "MET", "MPC", "CMG", "EA",
        "AXON", "RDDT", "AME", "HEI", "EW", "D", "BKR", "GWW", "FER",
        "DEO", "TGT", "ROP", "DAL", "AU", "FAST", "AMP", "CTVA", "ROK",
        "MPWR", "OKE", "HLN", "CARR", "CCJ", "MSCI", "FERG", "IMO", "EXC",
        "WCN", "XEL", "TEAM", "CPNG", "CUK", "FNV", "SYM", "CCL", "AIG", "HEI.A",
        "A", "YUM", "LVS", "IQV", "ETR", "GFI", "DHI", "PUK", "PRU", "OXY", "CTSH",
        "EBAY", "GRMN", "PAYX", "ALC", "MCHP", "VEEV", "TKO", "GEHC",
        "PEG", "VMC", "CCEP", "HMC", "TRGP", "EL", "HIG", "MLM", "NUE",
        "FICO", "NOK", "KR", "WAB", "CPRT", "FISV", "TEVA", "KDP",
        "FLUT", "KGC", "ZS", "KEYS", "HSY", "RYAAY", "EXPE", "CIEN", "FIX", "RMD",
        "MDB", "ED", "SLF", "NTRA", "MT", "CLS", "ODFL", "SYY",
        "FIS", "OTIS", "TER", "PCG", "UI", "ACGL", "WEC", "EQT", "XYL",
        "LYV", "HUM", "IX", "ERIC", "VIK", "FOXA", "COHR", "VOD", "RJF", "KMB",
        "IR", "FITB", "MTB", "IBKR", "KVUE", "WTW", "SYF",
        "DG", "WIT", "STLA", "VRSK", "QSR", "CHTR", "HPE", "MTD",
        "NTR", "EME", "ESLT", "LPLA", "ULTA", "ROL", "NRG", "HBAN",
        "LITE", "ADM", "ALAB", "DXCM", "DOV", "AFRM", "KHC", "PHG", "TPR",
        "FCNCA", "MKL", "BIIB", "BRO", "CBOE", "AEE", "ATO", "DTE", "TSCO",
        "CFG", "BE", "EFX", "DLTR", "FSLR",
        "STM", "WRB", "FTS"
    ]

    reit_tickers = [
        "ADC", "AHR", "AMH", "AMT", "ARE", "AVB", "BRX", "BXP", "CBRE", "CCI", "CPT", "CSGP", 
        "CTRE", "CUBE", "CUZ", "DLR", "DOC", "EGP", "ELS", "EPRT", "EQIX", "EQR", "ESS", "EXR", 
        "FR", "FRMI", "FRT", "FSP", "GLPI", "HR", "HST", "INVH", "IRM", "IRT", "KIM", "KRC", 
        "KRG", "LAMR", "LINE", "MAA", "MAC", "MRP", "NNN", "O", "OHI", "ONL", "OUT", "PECO", 
        "PLD", "PSA", "REG", "REXR", "RHP", "SBAC", "SBRA", "SELF", "SKT", "SPG", "STAG", "SUI", 
        "TRNO", "UDR", "VICI", "VNO", "VTR", "WELL", "WPC", "WY"
    ]

    brazilian_etfs = ["BOVA11.SA", "SPXR11.SA", "LFTB11.SA", "AREA11.SA", "DIVO11.SA", "B5MB11.SA", "DOLA11.SA", "AUPO11.SA"]
    american_etfs = ["BTCI", "DIVO", "GLD", "GPIQ", "IBIT", "JEPQ", "MCHI", "QDVO", 
                     "QQQM", "SLV", "SPYI", "VIG", "VOO", "VT", "VUG"]
    
    all_tickers = brazilian_tickers + american_tickers + reit_tickers + brazilian_etfs + american_etfs
    results = []

    print(f"--- Starting Analysis for {len(all_tickers)} Tickers ---")

    for ticker in all_tickers:
        try:
            print(f"--- Processing {ticker} ---")
            asset = yf.Ticker(ticker)
            info = asset.info

            tag, price_prefix = '', ''
            if ticker in brazilian_tickers:
                tag = 'Ação Brasileira'
                price_prefix = 'R$'
            elif ticker in american_tickers:
                tag = 'Ação Americana'
                price_prefix = 'U$'
            elif ticker in reit_tickers:
                tag = 'REIT'
                price_prefix = 'U$'
            elif ticker in brazilian_etfs:
                tag = 'ETF Brasileiro'
                price_prefix = 'R$'
            elif ticker in american_etfs:
                tag = 'ETF Americano'
                price_prefix = 'U$'

            current_price = info.get('regularMarketPrice')
            formatted_current_price = f"{price_prefix} {current_price:.2f}" if current_price is not None else "N/A"

            if tag in ['ETF Brasileiro', 'ETF Americano']:
                results.append({
                    'Ticker': ticker,
                    'Tag': tag,
                    'Preço Atual': formatted_current_price,
                    'P/FCO (O)': 'N/A', 'Preço Alvo': 'N/A', 'T (Alvo/Preço)': 'N/A',
                    'Compra Forte': 'N/A', 'Compra': 'N/A', 'Neutro': 'N/A', 'Venda': 'N/A', 'Venda Forte': 'N/A',
                    'R': 'N/A', 'C': 'N/A'
                })
                print(f"Successfully processed {tag}: {ticker}")
                continue

            p_fco_ratio = None
            try:
                cashflow = asset.get_cashflow()
                if not cashflow.empty and 'OperatingCashFlow' in cashflow.index:
                    operating_cash_flow = cashflow.loc['OperatingCashFlow'].iloc[0]
                    shares_outstanding = info.get('sharesOutstanding')
                    if operating_cash_flow and shares_outstanding > 0:
                        fco_per_share = operating_cash_flow / shares_outstanding
                        if current_price and fco_per_share > 0:
                            p_fco_ratio = current_price / fco_per_share
            except Exception: pass

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
            c_metric = (t_ratio * r_value) / p_fco_ratio if t_ratio and r_value and p_fco_ratio and p_fco_ratio != 0 else None

            results.append({
                'Ticker': ticker, 'Tag': tag, 'Preço Atual': formatted_current_price,
                'P/FCO (O)': p_fco_ratio, 'Preço Alvo': formatted_target_price, 'T (Alvo/Preço)': t_ratio,
                'Compra Forte': strong_buy, 'Compra': buy, 'Neutro': hold, 'Venda': sell, 'Venda Forte': strong_sell,
                'R': r_value, 'C': c_metric
            })
            print(f"Successfully processed {tag}: {ticker}")

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
