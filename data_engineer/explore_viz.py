"""
Quick data exploration visualization — NYC Taxi Customer Behavior Segmentation
Sesuai tujuan project: segmentasi perjalanan, analisis spasial, karakterisasi zona
Run: python explore_viz.py
Output: explore_viz.png
"""

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings("ignore")

FACT  = "data/intermediate/fact_trips.parquet"
ZONES = "data/intermediate/dim_zones.parquet"

con = duckdb.connect()

print("Loading data...")

# 1. Trip count per hour of day
hourly = con.execute(f"""
    SELECT pickup_hour, COUNT(*) AS trips
    FROM read_parquet('{FACT}')
    GROUP BY pickup_hour ORDER BY pickup_hour
""").fetchdf()

# 2. Trip count per borough
borough = con.execute(f"""
    SELECT pickup_borough, COUNT(*) AS trips
    FROM read_parquet('{FACT}')
    WHERE pickup_borough IS NOT NULL
    GROUP BY pickup_borough ORDER BY trips DESC
""").fetchdf()

# 3. Top 10 pickup zones
top_zones = con.execute(f"""
    SELECT pickup_zone, COUNT(*) AS trips
    FROM read_parquet('{FACT}')
    WHERE pickup_zone IS NOT NULL
    GROUP BY pickup_zone ORDER BY trips DESC LIMIT 10
""").fetchdf()

# 4. Tip rate distribution (sampled)
tip_dist = con.execute(f"""
    SELECT tip_rate_pct
    FROM read_parquet('{FACT}')
    WHERE tip_rate_pct > 0 AND tip_rate_pct < 100
    USING SAMPLE 50000
""").fetchdf()

# 5. Average tip rate per borough
tip_borough = con.execute(f"""
    SELECT pickup_borough,
           ROUND(AVG(tip_rate_pct), 1) AS avg_tip_rate,
           ROUND(AVG(trip_duration_min), 1) AS avg_duration
    FROM read_parquet('{FACT}')
    WHERE pickup_borough IS NOT NULL AND tip_rate_pct > 0
    GROUP BY pickup_borough ORDER BY avg_tip_rate DESC
""").fetchdf()

# 6. Trip count by time of day
tod = con.execute(f"""
    SELECT time_of_day,
           COUNT(*) AS trips,
           ROUND(AVG(tip_rate_pct), 1) AS avg_tip_rate
    FROM read_parquet('{FACT}')
    WHERE time_of_day IS NOT NULL
    GROUP BY time_of_day
    ORDER BY CASE time_of_day
        WHEN 'morning' THEN 1 WHEN 'afternoon' THEN 2
        WHEN 'evening' THEN 3 ELSE 4 END
""").fetchdf()

# 7. Rush hour vs non-rush
rush = con.execute(f"""
    SELECT is_rush_hour,
           COUNT(*) AS trips,
           ROUND(AVG(trip_duration_min), 1) AS avg_duration,
           ROUND(AVG(tip_rate_pct), 1) AS avg_tip
    FROM read_parquet('{FACT}')
    GROUP BY is_rush_hour
""").fetchdf()

con.close()

print("Rendering charts...")

fig = plt.figure(figsize=(18, 14))
fig.patch.set_facecolor('#0f0f1a')
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

PURPLE = '#7c4dff'
GOLD   = '#ffd740'
TEAL   = '#00bcd4'
colors = [PURPLE, GOLD, TEAL, '#ff5252', '#69f0ae']

def style_ax(ax, title):
    ax.set_facecolor('#1a1a2e')
    ax.set_title(title, color='white', fontsize=11, fontweight='bold', pad=8)
    ax.tick_params(colors='#aaaaaa', labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor('#333355')
    ax.xaxis.label.set_color('#aaaaaa')
    ax.yaxis.label.set_color('#aaaaaa')

# --- 1. Trips per hour ---
ax1 = fig.add_subplot(gs[0, :2])
bars = ax1.bar(hourly['pickup_hour'], hourly['trips'] / 1000,
               color=PURPLE, alpha=0.85, width=0.7)
ax1.set_xlabel('Hour of Day')
ax1.set_ylabel('Trips (thousands)')
ax1.set_xticks(range(0, 24))
style_ax(ax1, 'Trip Volume by Hour of Day')
ax1.axvspan(7, 9, alpha=0.15, color=GOLD, label='Rush hour')
ax1.axvspan(17, 19, alpha=0.15, color=GOLD)
ax1.legend(facecolor='#1a1a2e', labelcolor='white', fontsize=8)

# --- 2. Borough distribution ---
ax2 = fig.add_subplot(gs[0, 2])
wedge_colors = [PURPLE, GOLD, TEAL, '#ff5252', '#69f0ae']
wedges, texts, autotexts = ax2.pie(
    borough['trips'], labels=borough['pickup_borough'],
    autopct='%1.1f%%', colors=wedge_colors,
    textprops={'color': 'white', 'fontsize': 8}
)
for at in autotexts:
    at.set_fontsize(7)
style_ax(ax2, 'Trips by Borough')

# --- 3. Top 10 pickup zones ---
ax3 = fig.add_subplot(gs[1, :2])
ax3.barh(top_zones['pickup_zone'][::-1], top_zones['trips'][::-1] / 1000,
         color=TEAL, alpha=0.85)
ax3.set_xlabel('Trips (thousands)')
style_ax(ax3, 'Top 10 Pickup Zones')

# --- 4. Tip rate distribution ---
ax4 = fig.add_subplot(gs[1, 2])
ax4.hist(tip_dist['tip_rate_pct'], bins=40, color=GOLD, alpha=0.8, edgecolor='none')
ax4.set_xlabel('Tip Rate (%)')
ax4.set_ylabel('Count')
style_ax(ax4, 'Tip Rate Distribution')

# --- 5. Avg tip rate per borough ---
ax5 = fig.add_subplot(gs[2, 0])
bars5 = ax5.bar(tip_borough['pickup_borough'], tip_borough['avg_tip_rate'],
                color=colors[:len(tip_borough)], alpha=0.85)
ax5.set_ylabel('Avg Tip Rate (%)')
ax5.tick_params(axis='x', rotation=20, labelsize=7)
for bar, val in zip(bars5, tip_borough['avg_tip_rate']):
    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
             f'{val}%', ha='center', va='bottom', color='white', fontsize=7)
style_ax(ax5, 'Avg Tip Rate by Borough')

# --- 6. Trips by time of day ---
ax6 = fig.add_subplot(gs[2, 1])
ax6.bar(tod['time_of_day'], tod['trips'] / 1000,
        color=[PURPLE, TEAL, GOLD, '#ff5252'], alpha=0.85)
ax6.set_ylabel('Trips (thousands)')
style_ax(ax6, 'Trip Volume by Time of Day')

# --- 7. Rush hour comparison ---
ax7 = fig.add_subplot(gs[2, 2])
labels = ['Non-Rush', 'Rush Hour']
rush_sorted = rush.sort_values('is_rush_hour')
x = range(2)
w = 0.35
ax7.bar([i - w/2 for i in x], rush_sorted['avg_duration'], w,
        label='Avg Duration (min)', color=PURPLE, alpha=0.85)
ax7.bar([i + w/2 for i in x], rush_sorted['avg_tip'], w,
        label='Avg Tip Rate (%)', color=GOLD, alpha=0.85)
ax7.set_xticks(list(x))
ax7.set_xticklabels(labels)
ax7.legend(facecolor='#1a1a2e', labelcolor='white', fontsize=7)
style_ax(ax7, 'Rush Hour: Duration vs Tip Rate')

fig.suptitle(
    'NYC Yellow Taxi — Customer Behavior Segmentation\nData Exploration (Sept 2025 – Jan 2026 | 14.5M trips)',
    color='white', fontsize=14, fontweight='bold', y=0.98
)

plt.savefig('explore_viz.png', dpi=140, bbox_inches='tight',
            facecolor=fig.get_facecolor())
plt.close()
print("Done! Saved to explore_viz.png")
