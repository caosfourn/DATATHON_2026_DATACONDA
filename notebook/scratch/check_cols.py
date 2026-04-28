import pandas as pd, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data_dir = 'dataset/'
for f in ['customers.csv','orders.csv','order_items.csv','payments.csv','shipments.csv','returns.csv','products.csv','promotions.csv','web_traffic.csv','inventory.csv','reviews.csv','sales.csv']:
    df = pd.read_csv(data_dir + f, nrows=0)
    print(f"{f}: {list(df.columns)}")
