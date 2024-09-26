from flask import Flask, render_template
import requests

app = Flask(__name__)


# Fetch currency data from Open Exchange Rates API
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


@app.route('/')
def index():
    currencies = fetch_currency_data()  # Get currency codes and descriptions
    exchange_rates = fetch_exchange_rates('585050d494ac48fd97b94ee8f0ce4bf0')  # Replace with your actual API key

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
