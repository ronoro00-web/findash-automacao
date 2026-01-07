import yfinance as yf
import pandas as pd
import json
import os
import sys

def run_analysis():
    """Fetches stock data and saves it as a JavaScript file."""
    
    brazilian_tickers = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA"]
    american_tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    all_tickers = brazilian_tickers + american_tickers
    results = []

    print("--- Starting Stock Analysis with Failure Detection ---")

    for ticker in all_tickers:
        try:
            print(f"--- Processing {ticker} ---")
            stock = yf.Ticker(ticker)
            info = stock.info

            current_price = info.get('regularMarketPrice')
            
            cashflow = stock.get_cashflow()
            operating_cash_flow = None
            if not cashflow.empty and 'Operating Cash Flow' in cashflow.index:
                operating_cash_flow = cashflow.loc['Operating Cash Flow'].iloc[0]

            shares_outstanding = info.get('sharesOutstanding')
            
            fco_per_share = None
            p_fco_ratio = None
            if operating_cash_flow and shares_outstanding and shares_outstanding > 0:
                fco_per_share = operating_cash_flow / shares_outstanding
                if current_price and fco_per_share and fco_per_share > 0:
                    p_fco_ratio = current_price / fco_per_share

            # --- CRITICAL FAILURE CHECK ---
            if p_fco_ratio is None:
                debug_info = f"P/FCO is None for {ticker}. \n"
                debug_info += f"  - Current Price: {current_price}\n"
                debug_info += f"  - Operating Cash Flow: {operating_cash_flow}\n"
                debug_info += f"  - Shares Outstanding: {shares_outstanding}\n"
                debug_info += f"  - FCO per Share: {fco_per_share}\n"
                print(debug_info, file=sys.stderr) # Print to standard error
                sys.exit(debug_info) # Exit with a clear error message

            target_price = info.get('targetMeanPrice')
            t_ratio = None
            if target_price and current_price and current_price > 0:
                t_ratio = target_price / current_price

            recs = stock.recommendations
            strong_buy, buy, hold, sell, strong_sell = 0, 0, 0, 0, 0
            if recs is not None and not recs.empty:
                latest_recs = recs.iloc[-1]
                strong_buy = int(latest_recs.get('strongBuy', 0))
                buy = int(latest_recs.get('buy', 0))
                hold = int(latest_recs.get('hold', 0))
                sell = int(latest_recs.get('sell', 0))
                strong_sell = int(latest_recs.get('strongSell', 0))

            r_value = (strong_buy * 3) + buy + (hold * -1) + (sell * -3) + (strong_sell * -5)

            c_metric = None
            if t_ratio is not None and r_value is not None and p_fco_ratio is not None and p_fco_ratio != 0:
                c_metric = (t_ratio * r_value) / p_fco_ratio

            results.append({
                'Ticker': ticker,
                'Preço Atual': current_price,
                'P/FCO (O)': p_fco_ratio,
                'Preço Alvo': target_price,
                'T (Alvo/Preço)': t_ratio,
                'Compra Forte': strong_buy,
                'Compra': buy,
                'Neutro': hold,
                'Venda': sell,
                'Venda Forte': strong_sell,
                'R': r_value,
                'C': c_metric
            })
            print(f"Successfully processed {ticker}")
        except Exception as e:
            print(f'Could not process {ticker}: {e}', file=sys.stderr)
            sys.exit(f"An exception occurred while processing {ticker}: {e}")

    df = pd.DataFrame(results)
    json_data = df.to_json(orient='records', indent=4)
    output_path = 'public/stock_data.js'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(f"const stockData = {json_data};")

    print(f"Analysis complete. Data saved to {output_path}")

if __name__ == "__main__":
    run_analysis()
