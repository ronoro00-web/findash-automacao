import yfinance as yf
import pandas as pd
import json

def run_analysis():
    """Fetches stock data and saves it to a JSON file."""
    brazilian_tickers = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA"]
    american_tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    all_tickers = brazilian_tickers + american_tickers
    results = []

    print("Starting stock data analysis...")

    for ticker in all_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            current_price = info.get('regularMarketPrice')
            target_price = info.get('targetMeanPrice')
            
            cashflow = stock.get_cashflow()
            operating_cash_flow = None
            if not cashflow.empty:
                if 'Total Cash From Operating Activities' in cashflow.index:
                    operating_cash_flow = cashflow.loc['Total Cash From Operating Activities'].iloc[0]
                elif 'Cash Flow From Operating Activities' in cashflow.index:
                    operating_cash_flow = cashflow.loc['Cash Flow From Operating Activities'].iloc[0]

            shares_outstanding = info.get('sharesOutstanding')
            fco_per_share = None
            p_fco_ratio = None
            if operating_cash_flow and shares_outstanding and shares_outstanding > 0:
                fco_per_share = operating_cash_flow / shares_outstanding
                if current_price and fco_per_share > 0:
                    p_fco_ratio = current_price / fco_per_share

            t_ratio = None
            if target_price and current_price and current_price > 0:
                t_ratio = target_price / current_price

            recommendations = stock.recommendations
            strong_buy, buy, hold, sell, strong_sell = 0, 0, 0, 0, 0
            if recommendations is not None and not recommendations.empty:
                latest_recommendations = recommendations.iloc[-1]
                strong_buy = latest_recommendations.get('strongBuy', 0)
                buy = latest_recommendations.get('buy', 0)
                hold = latest_recommendations.get('hold', 0)
                sell = latest_recommendations.get('sell', 0)
                strong_sell = latest_recommendations.get('strongSell', 0)

            c_value = (strong_buy * 3) + buy + (hold * -1) + (sell * -3) + (strong_sell * -5)

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
                'C': c_value
            })
            print(f"Successfully processed {ticker}")
        except Exception as e:
            print(f'Could not process {ticker}: {e}')

    df = pd.DataFrame(results)
    json_data = df.to_json(orient='records', indent=4)
    
    # Save the data to the public folder, where the website can access it
    with open('public/stock_analysis.json', 'w') as f:
        f.write(json_data)

    print("Analysis complete. Data saved to public/stock_analysis.json")

if __name__ == "__main__":
    run_analysis()
