import yfinance as yf
import pandas as pd
import json
import os

def run_analysis():
    """Fetches stock data and saves it as a JavaScript file."""
    # Using a single ticker for focused debugging
    ticker = "AAPL"
    print(f"--- Starting Debugging for {ticker} ---")

    try:
        stock = yf.Ticker(ticker)
        
        # Get the cashflow statement
        cashflow = stock.get_cashflow()
        
        if not cashflow.empty:
            # Print all available index names from the cashflow report
            print("Available cashflow metrics:")
            print(list(cashflow.index))
        else:
            print("Cashflow data is empty.")

    except Exception as e:
        print(f'Could not process {ticker}: {e}')

    print(f"--- End Debugging for {ticker} ---")
    
    # We are stopping execution here for debugging, so no file will be written.
    # The main goal is to inspect the logs.

if __name__ == "__main__":
    run_analysis()
