# === 1.4 Spike Analysis - Phiên bản Gán nhãn bên phải chuyên nghiệp ===
daily_rev = sales.set_index('Date')['Revenue']

# 1. Xác định các ngưỡng
threshold = daily_rev.quantile(0.99)
spike_days = daily_rev[daily_rev >= threshold]
double_days_mask = ((daily_rev.index.month == 11) & (daily_rev.index.day == 11)) | \
                   ((daily_rev.index.month == 12) & (daily_rev.index.day == 12))
double_days = daily_rev[double_days_mask]

fig, ax = plt.subplots(figsize=(22, 9))

# 2. Vẽ dữ liệu nền
ax.plot(daily_rev.index, daily_rev.values, color='lightgray', alpha=0.15, linewidth=0.5)
ax.plot(daily_rev.rolling(30).mean().index, daily_rev.rolling(30).mean().values,
        color='#1f77b4', linewidth=3, label='Xu hướng (MA 30 ngày)', zorder=2)

# 3. Vẽ các điểm bùng nổ
ax.scatter(spike_days.index, spike_days.values, color='#d62728', s=55, zorder=5, 
           edgecolor='white', label='Kỷ lục Mùa vụ (Top 1%)')
ax.scatter(double_days.index, double_days.values, color='#ff7f0e', marker='D', s=50, zorder=6, 
           edgecolor='white', label='Sự kiện Double Days (11/11, 12/12)')

# --- GIẢI PHÁP CHỐNG TRÀN KHUNG & CHỒNG CHÉO ---
# Nới rộng trục X về bên phải (khoảng 150 ngày) và trục Y (40%) để lấy chỗ ghi chú
ax.set_xlim(daily_rev.index.min(), daily_rev.index.max() + timedelta(days=150))
ax.set_ylim(0, daily_rev.max() * 1.4)

# Chọn lọc các đỉnh tiêu biểu để tránh rối mắt (Top 8 đỉnh và Top 5 Double Days)
highlights = pd.concat([spike_days.sort_values(ascending=False).head(8), 
                        double_days.sort_values(ascending=False).head(5)]).index.unique().sort_values()

for i, dt in enumerate(highlights):
    rev = daily_rev[dt]
    before_7d = daily_rev[(daily_rev.index >= dt - timedelta(days=7)) & (daily_rev.index < dt)].mean()
    multiplier = rev / before_7d if before_7d > 0 else 0
    
    label = f"{dt.strftime('%m/%d')}\n{rev/1e6:.1f}M ({multiplier:.1f}x)"
    color = '#d62728' if dt in spike_days.index else '#ff7f0e'
    
    # Kỹ thuật gán sang PHẢI với độ cao so le (Staggered)
    x_offset = 35 
    y_offset = (i % 3 - 1) * 30 # Tạo ra 3 tầng vị trí: -30, 0, 30 để tránh dính nhau
    
    ax.annotate(label, 
                xy=(dt, rev), 
                xytext=(x_offset, y_offset), 
                textcoords='offset points', 
                fontsize=9, ha='left', va='center', 
                color=color, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=color, alpha=0.9),
                arrowprops=dict(arrowstyle='->', color=color, alpha=0.4, 
                                connectionstyle="arc3,rad=0.1")) # Đường dẫn hơi cong

# 4. Định dạng biểu đồ
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x/1e6:.0f}M'))

ax.set_title('Phân tích Điểm bùng nổ Doanh thu: Mùa vụ vs. Mega Sale', fontsize=18, fontweight='bold', pad=25)
ax.legend(loc='upper left', frameon=True, shadow=True)
plt.grid(axis='both', linestyle=':', alpha=0.3)
plt.tight_layout()
plt.show()

# --- BẢNG BÁO CÁO TÓM TẮT ---
print(f"\n{'NGÀY':<12} | {'LOẠI SỰ KIỆN':<18} | {'REVENUE':<12} | {'UPLIFT':<8} | {'CANNIBAL.'}")
print("-" * 70)
report_days = highlights[::-1] # In từ mới nhất đến cũ nhất
for dt in report_days:
    rev = daily_rev[dt]
    event = "SEASONAL PEAK" if rev >= threshold else "DOUBLE DAY"
    before = daily_rev[(daily_rev.index >= dt - timedelta(days=7)) & (daily_rev.index < dt)].mean()
    after = daily_rev[(daily_rev.index > dt) & (daily_rev.index <= dt + timedelta(days=7))].mean()
    up = rev / before if before > 0 else 0
    can = (after - before) / before * 100 if before > 0 else 0
    print(f"{str(dt.date()):<12} | {event:<18} | {rev:>11,.0f} | {up:>6.1f}x | {can:>9.1f}%")