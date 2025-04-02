from flask import Flask, render_template, request, jsonify
import sqlite3
import requests
from datetime import datetime

app = Flask(__name__)


# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('currency.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rates
                 (currency TEXT PRIMARY KEY, 
                  rate REAL, 
                  updated_at TEXT)''')
    conn.commit()
    conn.close()


# Получение курсов валют
def fetch_rates():
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()

        # Основные валюты + RUB, CHF, CNY
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'RUB', 'CHF', 'CNY']
        rates = {curr: data['rates'][curr] for curr in currencies if curr in data['rates']}

        updated_at = datetime.now().isoformat()

        conn = sqlite3.connect('currency.db')
        c = conn.cursor()
        for currency, rate in rates.items():
            c.execute('''INSERT OR REPLACE INTO rates 
                         VALUES (?, ?, ?)''',
                      (currency, rate, updated_at))
        conn.commit()
        conn.close()
        return True, updated_at
    except Exception as e:
        print(f"Ошибка при обновлении курсов: {str(e)}")
        return False, None


# Получение времени последнего обновления
def get_last_update():
    try:
        conn = sqlite3.connect('currency.db')
        c = conn.cursor()
        c.execute('SELECT updated_at FROM rates LIMIT 1')
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Ошибка при получении времени обновления: {str(e)}")
        return None


# Конвертация валют
def convert_currency(from_curr, to_curr, amount):
    try:
        amount = float(amount)
        conn = sqlite3.connect('currency.db')
        c = conn.cursor()

        c.execute('SELECT rate FROM rates WHERE currency = ?', (from_curr,))
        from_rate = c.fetchone()

        c.execute('SELECT rate FROM rates WHERE currency = ?', (to_curr,))
        to_rate = c.fetchone()

        conn.close()

        if from_rate and to_rate:
            # Конвертация через USD как базовую валюту
            result = amount * (1 / float(from_rate[0])) * float(to_rate[0])
            return round(result, 4)
        return None
    except Exception as e:
        print(f"Ошибка конвертации: {str(e)}")
        return None


# Маршруты
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/update_rates', methods=['POST'])
def update_rates():
    success, updated_at = fetch_rates()
    if success:
        return jsonify({
            'status': 'success',
            'updated_at': updated_at,
            'message': 'Курсы успешно обновлены'
        })
    return jsonify({
        'status': 'error',
        'message': 'Не удалось обновить курсы'
    }), 500


@app.route('/api/last_update')
def last_update():
    updated_at = get_last_update()
    if updated_at:
        return jsonify({
            'status': 'success',
            'updated_at': updated_at
        })
    return jsonify({
        'status': 'error',
        'message': 'Данные еще не обновлялись'
    }), 404


@app.route('/api/convert', methods=['POST'])
def convert():
    data = request.get_json()
    if not data:
        return jsonify({
            'status': 'error',
            'message': 'Не получены данные'
        }), 400

    from_curr = data.get('from')
    to_curr = data.get('to')
    amount = data.get('amount')

    if not all([from_curr, to_curr, amount]):
        return jsonify({
            'status': 'error',
            'message': 'Не все параметры указаны'
        }), 400

    try:
        result = convert_currency(from_curr, to_curr, amount)
        if result is not None:
            return jsonify({
                'status': 'success',
                'result': result,
                'from': from_curr,
                'to': to_curr,
                'amount': amount
            })
        return jsonify({
            'status': 'error',
            'message': 'Не удалось выполнить конвертацию'
        }), 400
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ошибка сервера: {str(e)}'
        }), 500


if __name__ == '__main__':
    init_db()
    # При первом запуске загружаем курсы, если база пуста
    if not get_last_update():
        fetch_rates()
    app.run(debug=True)