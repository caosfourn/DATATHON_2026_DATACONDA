"""
Data loader module for the EDA Dashboard.
Replicates the data loading and transformation logic from the notebook.
Uses Streamlit caching for performance.
"""
import streamlit as st
import pandas as pd
import numpy as np
import os

from utils.constants import DATA_DIR


@st.cache_data(ttl=3600)
def get_data_dir():
    """Get the absolute path to the data directory."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, '..', 'dataset')


@st.cache_data(ttl=3600)
def load_raw_data():
    """Load all raw CSV files. Cached for performance."""
    data_dir = get_data_dir()

    data = {}
    data['customers'] = pd.read_csv(
        os.path.join(data_dir, 'customers.csv'), parse_dates=['signup_date']
    )
    data['orders'] = pd.read_csv(
        os.path.join(data_dir, 'orders.csv'), parse_dates=['order_date']
    )
    data['order_items'] = pd.read_csv(os.path.join(data_dir, 'order_items.csv'))
    data['payments'] = pd.read_csv(os.path.join(data_dir, 'payments.csv'))
    data['shipments'] = pd.read_csv(
        os.path.join(data_dir, 'shipments.csv'),
        parse_dates=['ship_date', 'delivery_date']
    )
    data['returns'] = pd.read_csv(
        os.path.join(data_dir, 'returns.csv'), parse_dates=['return_date']
    )
    data['products'] = pd.read_csv(os.path.join(data_dir, 'products.csv'))
    data['promotions'] = pd.read_csv(os.path.join(data_dir, 'promotions.csv'))
    data['web_traffic'] = pd.read_csv(
        os.path.join(data_dir, 'web_traffic.csv'), parse_dates=['date']
    )
    data['inventory'] = pd.read_csv(
        os.path.join(data_dir, 'inventory.csv'), parse_dates=['snapshot_date']
    )
    data['reviews'] = pd.read_csv(
        os.path.join(data_dir, 'reviews.csv'), parse_dates=['review_date']
    )
    data['sales'] = pd.read_csv(
        os.path.join(data_dir, 'sales.csv'), parse_dates=['Date']
    )
    data['geography'] = pd.read_csv(os.path.join(data_dir, 'geography.csv'))

    return data


@st.cache_data(ttl=3600)
def load_and_transform_data():
    """
    Load data and apply all transformations from Phase 0 of the notebook.
    Returns a dictionary of transformed DataFrames.
    """
    data = load_raw_data()

    customers = data['customers'].copy()
    orders = data['orders'].copy()
    order_items = data['order_items'].copy()
    payments = data['payments'].copy()
    shipments = data['shipments'].copy()
    returns = data['returns'].copy()
    products = data['products'].copy()
    promotions = data['promotions'].copy()
    web_traffic = data['web_traffic'].copy()
    inventory = data['inventory'].copy()
    reviews = data['reviews'].copy()
    sales = data['sales'].copy()
    geography = data['geography'].copy()

    # === 1. Fix Signup Date Anomaly ===
    first_orders = orders.groupby('customer_id')['order_date'].min().reset_index(
        name='first_order_date'
    )
    customers = customers.merge(first_orders, on='customer_id', how='left')
    anomaly_pct = (
        (customers['first_order_date'] < customers['signup_date']).mean() * 100
    )
    customers['true_signup_date'] = np.where(
        customers['first_order_date'] < customers['signup_date'],
        customers['first_order_date'],
        customers['signup_date'],
    )
    customers['true_signup_date'] = pd.to_datetime(customers['true_signup_date'])

    # === 2. Calculate total_amount for orders from payments ===
    if 'total_amount' not in orders.columns:
        order_totals = (
            payments.groupby('order_id')['payment_value'].sum().rename('total_amount')
        )
        orders = orders.join(order_totals, on='order_id')

    # === 3. Feature Engineering ===
    orders['order_month'] = orders['order_date'].dt.to_period('M').dt.to_timestamp()
    orders['order_quarter'] = orders['order_date'].dt.quarter
    orders['order_year'] = orders['order_date'].dt.year
    orders['day_of_week'] = orders['order_date'].dt.dayofweek
    orders['is_weekend'] = orders['day_of_week'].isin([5, 6]).astype(int)

    # Delivery time features
    ship_data = shipments.copy()
    ship_data['delivery_time'] = (
        ship_data['delivery_date'] - ship_data['ship_date']
    ).dt.days

    # Item-level revenue & profit
    order_items['item_revenue'] = (
        order_items['quantity'] * order_items['unit_price']
        - order_items['discount_amount'].fillna(0)
    )
    oi_with_cogs = order_items.merge(
        products[['product_id', 'cogs']], on='product_id', how='left'
    )
    order_items['item_profit'] = (
        oi_with_cogs['quantity'] * oi_with_cogs['unit_price']
        - oi_with_cogs['discount_amount'].fillna(0)
        - oi_with_cogs['quantity'] * oi_with_cogs['cogs']
    )
    order_items['discount_rate'] = order_items['discount_amount'].fillna(0) / (
        order_items['quantity'] * order_items['unit_price']
    ).replace(0, np.nan)
    order_items['is_discounted'] = (
        order_items['discount_amount'].fillna(0) > 0
    ).astype(int)

    # Sales: Gross Profit
    sales['Gross_Profit'] = sales['Revenue'] - sales['COGS']
    sales['Gross_Margin'] = sales['Gross_Profit'] / sales['Revenue'].replace(0, np.nan)
    sales['YearMonth'] = sales['Date'].dt.to_period('M')

    # Orders delivered
    orders_delivered = orders[orders['order_status'] == 'delivered'].copy()

    # Merge geography
    if 'region' not in orders.columns:
        orders = orders.merge(
            geography[['zip', 'region', 'district']], on='zip', how='left'
        )

    result = {
        'customers': customers,
        'orders': orders,
        'order_items': order_items,
        'payments': payments,
        'shipments': shipments,
        'ship_data': ship_data,
        'returns': returns,
        'products': products,
        'promotions': promotions,
        'web_traffic': web_traffic,
        'inventory': inventory,
        'reviews': reviews,
        'sales': sales,
        'geography': geography,
        'orders_delivered': orders_delivered,
        'anomaly_pct': anomaly_pct,
    }

    return result


def get_data_summary(data):
    """Get a summary of all loaded datasets for the Data Quality tab."""
    raw = load_raw_data()
    summary = []
    for name, df in raw.items():
        summary.append({
            'Table': name,
            'Rows': len(df),
            'Columns': len(df.columns),
        })
    return pd.DataFrame(summary)


def get_missing_data_summary(data):
    """Calculate missing data statistics for each table/column."""
    raw = load_raw_data()
    missing_summary = []
    for name, df in raw.items():
        total = len(df)
        for col in df.columns:
            miss = df[col].isna().sum()
            if miss > 0:
                missing_summary.append({
                    'Table': name,
                    'Column': col,
                    'Missing': miss,
                    'Pct': round(miss / total * 100, 2),
                })
    return pd.DataFrame(missing_summary) if missing_summary else None


def get_duplicates_summary():
    """Check for duplicates in key tables."""
    raw = load_raw_data()
    dupes = []
    for name, df in [
        ('orders', raw['orders']),
        ('customers', raw['customers']),
        ('payments', raw['payments']),
    ]:
        pk = df.columns[0]
        d = df[pk].duplicated().sum()
        dupes.append({'Table': name, 'Primary Key': pk, 'Duplicates': d})
    return pd.DataFrame(dupes)
