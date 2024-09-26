from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import mysql.connector
from mysql.connector import Error
import requests

app = Flask(__name__)

@app.route("/")
def home_page():
    return render_template("index.html")

DB_CONFIG = {
    'host': 'localhost',  # Change if necessary
    'user': 'root',
    'password': 'root123',
    'database': 'hackathon'
}

# Load exchange rate data from the MySQL database
def load_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            query = "SELECT * FROM final_data"
            df = pd.read_sql(query, conn)
            df['Date'] = pd.to_datetime(df['Date'])  # Convert to datetime
            df.set_index('Date', inplace=True)
            return df
    except Error as e:
        print(f"Error: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
    finally:
        if conn.is_connected():
            conn.close()

# Generate chart using Plotly based on selected currency, year, and duration
def create_plotly_chart(df, currency, duration):
    df_filtered = df[[currency]]

    # Resample data based on the selected duration
    if duration == 'weekly':
        df_resampled = df_filtered.resample('W').mean()
    elif duration == 'monthly':
        df_resampled = df_filtered.resample('M').mean()
    elif duration == 'quarterly':
        df_resampled = df_filtered.resample('Q').mean()
    elif duration == 'yearly':
        df_resampled = df_filtered.resample('Y').mean()
    else:
        df_resampled = df_filtered  # No resampling

    # Create Plotly figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_resampled.index, y=df_resampled[currency],
                             mode='lines+markers', name=currency))

    fig.update_layout(
        title=f"Exchange Rate Trend for {currency} ({duration.capitalize()})",
        xaxis_title='Date',
        yaxis_title='Exchange Rate',
        template='plotly_white',
        hovermode='x unified'
    )

    # Generate HTML div with Plotly chart
    graph_html = pio.to_html(fig, full_html=False)

    return graph_html

@app.route('/dashboard', methods=['GET', 'POST'])
def index():
    df = load_data()
    currencies = df.columns.to_list()
    print(currencies)
    if request.method == 'POST':
        currency = request.form['currency']
        duration = request.form['duration']
        selected_year = int(request.form['year'])

        # Filter data based on the selected year
        df_filtered = df[df.index.year == selected_year]

        # Check if the filtered DataFrame is empty
        if df_filtered.empty:
            return render_template('task1.html', currencies=currencies, error="No data available for the selected year.")

        # Create chart based on user selection
        chart = create_plotly_chart(df_filtered, currency, duration)

        # Get max and min exchange rates and their corresponding dates for the filtered year
        highest_rate = df_filtered[currency].max()
        highest_date = df_filtered[df_filtered[currency] == highest_rate].index[0]
        lowest_rate = df_filtered[currency].min()
        lowest_date = df_filtered[df_filtered[currency] == lowest_rate].index[0]

        #print(f"Filtered Data for {currency} in {selected_year}:")
        print(df_filtered[currency])  # This will show the relevant rates for the selected year
        print(f"Highest Rate: {highest_rate} on {highest_date}")
        print(f"Lowest Rate: {lowest_rate} on {lowest_date}")

        # Convert dates to readable format
        highest_date_value = highest_date.strftime("%Y-%m-%d")
        lowest_date_value = lowest_date.strftime("%Y-%m-%d")

        # Display the statistics and chart in the template
        return render_template('task1.html', chart=chart, highest_rate=highest_rate,
                               highest_date=highest_date_value, lowest_rate=lowest_rate,
                               lowest_date=lowest_date_value, currency=currency,
                               currencies=currencies, year=selected_year,
                               duration=duration, selected_year=selected_year)

    # Render form for the first time
    return render_template('task1.html', currencies=currencies)

@app.route("/task2")
def display_tsk2():
    return render_template("task2.html")
@app.route('/custom-basket', methods=['GET', 'POST'])
def custom_basket():
    df = load_data()
    currencies = df.columns.to_list()

    if request.method == 'POST':
        # Get the number of currencies to add from the user
        num_currencies = int(request.form.get('num_currencies'))
        return render_template('custom_basket.html', currencies=currencies, num_currencies=num_currencies)

    # Initial page load, no num_currencies yet
    return render_template('custom_basket.html', currencies=currencies, num_currencies=None)


@app.route('/custom-basket-values', methods=['POST'])
def custom_basket_values():
    df = load_data()
    currencies = df.columns.to_list()

    base_currency = request.form['base_currency']
    num_currencies = int(request.form.get('num_currencies'))
    total_basket_value = 0

    # Loop through the number of currencies and retrieve values
    for i in range(1, num_currencies + 1):
        currency = request.form.get(f'currency{i}')
        weight = request.form.get(f'weight{i}', 0)
        weight = float(weight) if weight else 0

        if currency and weight > 0:
            latest_rate = df[currency].iloc[-1]  # Get the latest exchange rate
            total_basket_value += latest_rate * (weight)  # Convert weight to fraction

    # Get the latest exchange rate for the base currency to convert basket value
    base_latest_rate = df[base_currency].iloc[-1]
    basket_value_in_base = total_basket_value * base_latest_rate

    # Render the result on the same custom basket page
    return render_template('custom_basket.html', currencies=currencies, basket_value=basket_value_in_base,
                           num_currencies=num_currencies)
@app.route("/task3", methods=["GET", "POST"])
def task3():
    df = load_data()  # Load the entire dataset into the DataFrame
    currencies = df.columns.to_list()  # Get a list of all currency columns

    risk_level = None
    plot_html = None

    if request.method == "POST":
        currency1 = request.form.get("currency1")
        currency2 = request.form.get("currency2")
        start_year = int(request.form.get("start_year"))
        end_year = int(request.form.get("end_year"))

        # Filter the data for the selected date range and currencies
        df_filtered = df.loc[(df.index.year >= start_year) & (df.index.year <= end_year), [currency1, currency2]]

        # Drop any rows with NaN values to prevent errors in percentage change calculations
        df_filtered.dropna(inplace=True)

        # Calculate percentage changes (returns) for each currency separately
        df_filtered['Return1'] = df_filtered[currency1].pct_change()
        df_filtered['Return2'] = df_filtered[currency2].pct_change()

        # Drop NaN values after pct_change
        df_filtered.dropna(inplace=True)

        # Calculate rolling volatility (standard deviation of returns) for each currency
        df_filtered['Volatility1'] = df_filtered['Return1'].rolling(window=60).std()
        df_filtered['Volatility2'] = df_filtered['Return2'].rolling(window=60).std()

        # Drop NaN values after rolling
        df_filtered.dropna(inplace=True)

        # Determine risk level based on final volatility value
        latest_volatility1 = df_filtered['Volatility1'].iloc[-1] if not df_filtered['Volatility1'].empty else 0
        latest_volatility2 = df_filtered['Volatility2'].iloc[-1] if not df_filtered['Volatility2'].empty else 0
        print(latest_volatility1)
        print(latest_volatility2)
        formatted_value1 = float(f"{latest_volatility1:.2f}")
        formatted_value2 = float(f"{latest_volatility2:.2f}")
        print(formatted_value1)
        print(formatted_value2)

        risk_currency1 = classify_risk(formatted_value1)
        risk_currency2 = classify_risk(formatted_value2)

        risk_level = {
            "currency1": currency1,
            "risk1": risk_currency1,
            "currency2": currency2,
            "risk2": risk_currency2
        }

        # Plot the rolling volatility using Plotly
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['Volatility1'], mode='lines+markers', name=f'{currency1} Volatility'))
        fig.add_trace(go.Scatter(x=df_filtered.index, y=df_filtered['Volatility2'], mode='lines+markers', name=f'{currency2} Volatility'))

        fig.update_layout(
            title=f'Fluctuation of {currency1} and {currency2} from {start_year} to {end_year}',
            xaxis_title='Date',
            yaxis_title='Volatility',
            template='plotly_white'
        )

        # Save the plot to the 'static' directory and return HTML for the plot
        plot_html = pio.to_html(fig, full_html=False)

        return render_template("task3.html", currencies=currencies, plot=plot_html, risk_level=risk_level)

    return render_template("task3.html", currencies=currencies)
def classify_risk(volatility):
    """Classify the risk level based on volatility."""
    if volatility < 0.01:
        return "Low"
    elif 0.01 <= volatility <= 0.02:
        return "Medium"
    else:
        return "High"

def fetch_currency_data():
    api_url = "https://openexchangerates.org/api/currencies.json"  # Endpoint for currency codes and descriptions
    response = requests.get(api_url)

    if response.status_code != 200:
        print("Error fetching currency codes:", response.status_code, response.text)
        return []

    currencies = response.json()  # Get currency codes and descriptions as a dictionary
    return currencies  # This will return something like {'USD': 'United States Dollar', ...}


# Fetch exchange rates from Open Exchange Rates
def fetch_exchange_rates(api_key):
    api_url = f"https://openexchangerates.org/api/latest.json?app_id={api_key}"
    response = requests.get(api_url)

    if response.status_code != 200:
        print("Error fetching exchange rates:", response.status_code, response.text)
        return {}

    data = response.json()
    return data['rates'] if 'rates' in data else {}


@app.route('/task4')
def display_task4():
    currencies = fetch_currency_data()
    exchange_rates = fetch_exchange_rates('585050d494ac48fd97b94ee8f0ce4bf0')

    # Create a list of currencies with their rates
    currency_list = []
    for code, description in currencies.items():
        if code in exchange_rates:  # Only include currencies that have rates
            currency_list.append({
                "code": code,
                "description": description,
                "rate": exchange_rates[code]  # Current exchange rate against USD
            })

    return render_template('task4.html', currencies=currency_list)


if __name__ == '__main__':
    app.run(debug=True)
