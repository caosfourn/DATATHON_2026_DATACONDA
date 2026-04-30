import pandas as pd
import numpy as np

oi = pd.read_csv('dataset/order_items.csv', low_memory=False)
orders = pd.read_csv('dataset/orders.csv')
products = pd.read_csv('dataset/products.csv')
promo = pd.read_csv('dataset/promotions.csv')

# Merge for analysis
merged = oi.merge(orders[['order_id','order_date','order_status']], on='order_id')
merged = merged.merge(products[['product_id','product_name','category','segment','price','cogs']], on='product_id')
merged = merged.merge(promo[['promo_id','promo_name','promo_type','discount_value']], on='promo_id', how='left')

# Filter delivered orders only
delivered = merged[merged['order_status']=='delivered'].copy()

# Check promo vs non-promo
has_promo = delivered[delivered['promo_id'].notna()]
no_promo = delivered[delivered['promo_id'].isna()]

print('=== OVERVIEW ===')
print(f'Total delivered items: {len(delivered):,}')
print(f'With promo: {len(has_promo):,} ({len(has_promo)/len(delivered)*100:.1f}%)')
print(f'Without promo: {len(no_promo):,} ({len(no_promo)/len(delivered)*100:.1f}%)')
print()

# Revenue calculations
delivered['gross_revenue'] = delivered['quantity'] * delivered['unit_price']
delivered['total_cogs'] = delivered['quantity'] * delivered['cogs']
delivered['original_revenue'] = delivered['quantity'] * delivered['price']
delivered['effective_discount_pct'] = np.where(
    delivered['original_revenue'] > 0,
    delivered['discount_amount'] / delivered['original_revenue'] * 100,
    0
)

has_promo2 = delivered[delivered['promo_id'].notna()]
no_promo2 = delivered[delivered['promo_id'].isna()]

print('=== AVG ORDER VALUE ===')
print(f"With promo - avg line revenue: {has_promo2['gross_revenue'].mean():,.0f}")
print(f"Without promo - avg line revenue: {no_promo2['gross_revenue'].mean():,.0f}")
print()

print('=== AVG QUANTITY ===')
print(f"With promo - avg qty: {has_promo2['quantity'].mean():.2f}")
print(f"Without promo - avg qty: {no_promo2['quantity'].mean():.2f}")
print()

# By category
print('=== BY CATEGORY ===')
for cat in sorted(products['category'].unique()):
    promo_cat = has_promo2[has_promo2['category']==cat]
    no_promo_cat = no_promo2[no_promo2['category']==cat]
    if len(promo_cat) > 0 and len(no_promo_cat) > 0:
        print(f"{cat}: Promo items={len(promo_cat):,}, No promo items={len(no_promo_cat):,}, "
              f"Promo avg qty={promo_cat['quantity'].mean():.2f}, No promo avg qty={no_promo_cat['quantity'].mean():.2f}")

print()
print('=== BY DISCOUNT LEVEL ===')
for dv in sorted(promo['discount_value'].unique()):
    subset = has_promo2[has_promo2['discount_value']==dv]
    if len(subset) > 0:
        print(f"Discount {dv}: items={len(subset):,}, avg_qty={subset['quantity'].mean():.2f}, "
              f"avg_revenue={subset['gross_revenue'].mean():,.0f}, avg_discount_amt={subset['discount_amount'].mean():,.0f}")

print()
print('=== PRICE ELASTICITY BY CATEGORY ===')
# Calculate daily order counts for promo vs non-promo periods
delivered['order_date'] = pd.to_datetime(delivered['order_date'])

for cat in sorted(products['category'].unique()):
    cat_data = delivered[delivered['category']==cat]
    
    # Daily orders during promo vs non-promo
    promo_daily = cat_data[cat_data['promo_id'].notna()].groupby('order_date')['order_id'].nunique()
    no_promo_daily = cat_data[cat_data['promo_id'].isna()].groupby('order_date')['order_id'].nunique()
    
    if len(promo_daily) > 0 and len(no_promo_daily) > 0:
        avg_promo = promo_daily.mean()
        avg_no_promo = no_promo_daily.mean()
        lift = (avg_promo - avg_no_promo) / avg_no_promo * 100
        
        # Avg effective discount
        avg_disc = cat_data[cat_data['promo_id'].notna()]['effective_discount_pct'].mean()
        
        # Elasticity = % change in quantity / % change in price
        if avg_disc > 0:
            elasticity = lift / avg_disc
            print(f"{cat}: Avg discount={avg_disc:.1f}%, Order lift={lift:.1f}%, Elasticity={elasticity:.2f}")

print()
print('=== PROFIT ANALYSIS ===')
# Gross profit analysis
delivered['gross_profit'] = delivered['gross_revenue'] - delivered['total_cogs']
delivered['margin_pct'] = delivered['gross_profit'] / delivered['gross_revenue'] * 100

for dv in sorted(promo['discount_value'].unique()):
    subset = has_promo2.copy()
    subset['gross_revenue'] = subset['quantity'] * subset['unit_price']
    subset['total_cogs'] = subset['quantity'] * subset['cogs']
    subset['gross_profit'] = subset['gross_revenue'] - subset['total_cogs']
    subset['margin_pct'] = subset['gross_profit'] / subset['gross_revenue'] * 100
    
    disc_subset = subset[subset['discount_value']==dv]
    if len(disc_subset) > 0:
        print(f"Discount {dv}: avg_margin={disc_subset['margin_pct'].mean():.1f}%, "
              f"total_profit={disc_subset['gross_profit'].sum():,.0f}, "
              f"total_revenue={disc_subset['gross_revenue'].sum():,.0f}")

# Non-promo margin
no_promo2_calc = no_promo2.copy()
no_promo2_calc['gross_revenue'] = no_promo2_calc['quantity'] * no_promo2_calc['unit_price']
no_promo2_calc['total_cogs'] = no_promo2_calc['quantity'] * no_promo2_calc['cogs']
no_promo2_calc['gross_profit'] = no_promo2_calc['gross_revenue'] - no_promo2_calc['total_cogs']
no_promo2_calc['margin_pct'] = no_promo2_calc['gross_profit'] / no_promo2_calc['gross_revenue'] * 100
print(f"No Promo: avg_margin={no_promo2_calc['margin_pct'].mean():.1f}%, "
      f"total_profit={no_promo2_calc['gross_profit'].sum():,.0f}, "
      f"total_revenue={no_promo2_calc['gross_revenue'].sum():,.0f}")

print()
print('=== CATEGORIES LIST ===')
print(products['category'].unique().tolist())
print()
print('=== SEGMENTS LIST ===')
print(products['segment'].unique().tolist())
