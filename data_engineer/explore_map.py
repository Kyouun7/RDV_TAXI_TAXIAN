"""
Explore map — NYC Taxi Customer Behavior Segmentation
Output: explore_map.html  (buka di browser)
Run:    python explore_map.py
"""

import duckdb
import json
import folium
from pathlib import Path

FACT_FILE    = "data/intermediate/fact_trips.parquet"
GEOJSON_FILE = "data/raw/zones/taxi_zones.geojson"

# --- Aggregate per zone ---
print("Aggregating data per zone...")
con = duckdb.connect()
zone_stats = con.execute(f"""
    SELECT
        pickup_location_id                  AS zone_id,
        pickup_zone                         AS zone_name,
        pickup_borough                      AS borough,
        COUNT(*)                            AS trip_count,
        ROUND(AVG(tip_rate_pct), 2)         AS avg_tip_rate,
        ROUND(AVG(trip_duration_min), 2)    AS avg_duration_min,
        ROUND(AVG(trip_distance), 2)        AS avg_distance_mi,
        ROUND(AVG(avg_speed_mph), 2)        AS avg_speed_mph
    FROM read_parquet('{FACT_FILE}')
    WHERE pickup_location_id IS NOT NULL
    GROUP BY pickup_location_id, pickup_zone, pickup_borough
""").fetchdf()
con.close()

stats_dict = zone_stats.set_index('zone_id').to_dict('index')

# --- Load GeoJSON ---
print("Loading GeoJSON...")
with open(GEOJSON_FILE, encoding='utf-8') as f:
    geojson = json.load(f)

for feature in geojson['features']:
    loc_id = feature['properties'].get('LocationID') or feature['properties'].get('location_id')
    feature['properties']['LocationID'] = int(loc_id) if loc_id else None

# --- Build map (centered on Midtown Manhattan) ---
print("Building map...")
m = folium.Map(
    location=[40.7549, -73.9840],
    zoom_start=12,
    tiles='CartoDB dark_matter'
)

# ── Layer 1: Trip Volume Choropleth ──────────────────────────────────────────
choropleth_trips = folium.Choropleth(
    geo_data=geojson,
    data=zone_stats,
    columns=['zone_id', 'trip_count'],
    key_on='feature.properties.LocationID',
    fill_color='YlOrRd',
    fill_opacity=0.75,
    line_opacity=0.2,
    line_color='white',
    nan_fill_color='#1a1a2e',
    legend_name='Trip Volume',
    name='Trip Volume per Zone',
    highlight=True,
).add_to(m)
# Remove Folium's built-in colorbar (we use custom HTML legend below)
m._children.pop(choropleth_trips.color_scale.get_name(), None)

# ── Layer 2: Avg Tip Rate Choropleth ─────────────────────────────────────────
choropleth_tip = folium.Choropleth(
    geo_data=geojson,
    data=zone_stats,
    columns=['zone_id', 'avg_tip_rate'],
    key_on='feature.properties.LocationID',
    fill_color='PuBuGn',
    fill_opacity=0.75,
    line_opacity=0.2,
    line_color='white',
    nan_fill_color='#1a1a2e',
    legend_name='Avg Tip Rate (%)',
    name='Avg Tip Rate per Zone',
    show=False,
).add_to(m)
m._children.pop(choropleth_tip.color_scale.get_name(), None)

# ── Layer 3: Zone click popups ────────────────────────────────────────────────
detail_layer = folium.FeatureGroup(name='Zone Detail (klik zona)', show=True)
for feature in geojson['features']:
    loc_id = feature['properties'].get('LocationID')
    if loc_id and int(loc_id) in stats_dict:
        s = stats_dict[int(loc_id)]
        popup_html = f"""
        <div style='font-family:Arial;min-width:210px;background:#1a1a2e;color:white;
                    padding:14px;border-radius:8px;border:1px solid #7c4dff;'>
            <b style='color:#ffd740;font-size:14px;'>{s.get('zone_name', '—')}</b>
            <div style='color:#aaa;font-size:11px;margin:2px 0 8px;'>{s.get('borough', '—')}</div>
            <hr style='border:none;border-top:1px solid #333;margin:0 0 8px;'>
            <table style='width:100%;font-size:12px;border-collapse:collapse;'>
                <tr style='margin-bottom:4px;'>
                    <td style='color:#aaa;padding:3px 0;'>Total Trips</td>
                    <td style='text-align:right;'><b>{int(s['trip_count']):,}</b></td>
                </tr>
                <tr>
                    <td style='color:#aaa;padding:3px 0;'>Avg Tip Rate</td>
                    <td style='text-align:right;'><b style='color:#7ecfb3;'>{s['avg_tip_rate']}%</b></td>
                </tr>
                <tr>
                    <td style='color:#aaa;padding:3px 0;'>Avg Duration</td>
                    <td style='text-align:right;'><b>{s['avg_duration_min']} min</b></td>
                </tr>
                <tr>
                    <td style='color:#aaa;padding:3px 0;'>Avg Distance</td>
                    <td style='text-align:right;'><b>{s['avg_distance_mi']} mi</b></td>
                </tr>
                <tr>
                    <td style='color:#aaa;padding:3px 0;'>Avg Speed</td>
                    <td style='text-align:right;'><b>{s['avg_speed_mph']} mph</b></td>
                </tr>
            </table>
        </div>
        """
        folium.GeoJson(
            feature,
            style_function=lambda x: {
                'fillColor': 'transparent',
                'color': 'transparent',
                'weight': 0,
            },
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=folium.Tooltip(
                f"<b>{s.get('zone_name', '—')}</b><br>"
                f"{int(s['trip_count']):,} trips &nbsp;|&nbsp; {s['avg_tip_rate']}% tip",
                style=(
                    "background-color:#1a1a2e;color:white;font-size:11px;"
                    "border:1px solid #555;padding:6px 8px;border-radius:5px;"
                )
            )
        ).add_to(detail_layer)

detail_layer.add_to(m)

# Layer control — collapsed into small icon (no clutter)
folium.LayerControl(collapsed=True, position='topright').add_to(m)

# ── Title bar (top center) ────────────────────────────────────────────────────
title_html = """
<div style="
    position:fixed; top:10px; left:50%; transform:translateX(-50%);
    background:rgba(18,18,36,0.93); color:white;
    padding:10px 28px; border-radius:9px; border:1px solid #7c4dff;
    font-family:Arial; font-size:14px; font-weight:bold;
    z-index:9999; text-align:center; white-space:nowrap;
    box-shadow:0 3px 12px rgba(0,0,0,0.6);">
    NYC Yellow Taxi &mdash; Customer Behavior Segmentation
    <br>
    <span style='font-size:11px; color:#bbb; font-weight:normal;'>
        Sept 2025 &ndash; Jan 2026
        &nbsp;&bull;&nbsp; 14.5M trips
        &nbsp;&bull;&nbsp; Hover zona = info
        &nbsp;&bull;&nbsp; Klik zona = detail
    </span>
</div>
"""

# ── Custom legend (bottom-left, swaps when layer toggles) ────────────────────
legend_html = """
<div id="map-legend" style="
    position:fixed; bottom:36px; left:12px; z-index:9999;
    background:rgba(18,18,36,0.93); color:white;
    padding:14px 18px; border-radius:9px; border:1px solid #444;
    font-family:Arial; font-size:12px; min-width:190px;
    box-shadow:0 3px 12px rgba(0,0,0,0.5);">

  <!-- Legend for Trip Volume layer -->
  <div id="leg-trips">
    <b style="font-size:12px; letter-spacing:.3px;">Trip Volume per Zona</b>
    <div style="margin:9px 0 4px;">
      <div style="
          background: linear-gradient(to right, #ffffb2, #fecc5c, #fd8d3c, #f03b20, #bd0026);
          height:13px; border-radius:5px;"></div>
      <div style="display:flex; justify-content:space-between; margin-top:4px; color:#999; font-size:10px;">
        <span>Sedikit</span><span>Banyak</span>
      </div>
    </div>
    <div style="color:#777; font-size:10px; margin-top:6px;">
      Merah tua = zona dengan pickup terbanyak
    </div>
  </div>

  <!-- Legend for Tip Rate layer (hidden by default) -->
  <div id="leg-tip" style="display:none;">
    <b style="font-size:12px; letter-spacing:.3px;">Avg Tip Rate per Zona</b>
    <div style="margin:9px 0 4px;">
      <div style="
          background: linear-gradient(to right, #f7fcfd, #ccebc5, #7bccc4, #2b8cbe, #084081);
          height:13px; border-radius:5px;"></div>
      <div style="display:flex; justify-content:space-between; margin-top:4px; color:#999; font-size:10px;">
        <span>Rendah</span><span>Tinggi</span>
      </div>
    </div>
    <div style="color:#777; font-size:10px; margin-top:6px;">
      Biru tua = zona dengan tip rate tertinggi
    </div>
  </div>
</div>

<script>
// Swap legend when layer control checkbox changes
document.addEventListener('change', function(e) {
    if (e.target.type !== 'checkbox') return;
    // Small delay so Leaflet finishes toggling the layer first
    setTimeout(function() {
        // Walk all checkboxes in the layer control
        var boxes = document.querySelectorAll('.leaflet-control-layers-overlays input[type=checkbox]');
        var tripOn = false, tipOn = false;
        boxes.forEach(function(cb) {
            var label = cb.closest('label');
            if (!label) return;
            var txt = label.textContent.trim();
            if (txt.indexOf('Trip Volume') !== -1) tripOn = cb.checked;
            if (txt.indexOf('Tip Rate')    !== -1) tipOn  = cb.checked;
        });
        // If tip-rate layer is ON (and trips OFF), show tip legend; else show trips legend
        var showTip = tipOn && !tripOn;
        document.getElementById('leg-trips').style.display = showTip ? 'none'  : 'block';
        document.getElementById('leg-tip').style.display   = showTip ? 'block' : 'none';
    }, 80);
});
</script>
"""

# ── How-to hint (bottom-right) ────────────────────────────────────────────────
hint_html = """
<div style="
    position:fixed; bottom:36px; right:12px; z-index:9999;
    background:rgba(18,18,36,0.93); color:#bbb;
    padding:10px 14px; border-radius:9px; border:1px solid #333;
    font-family:Arial; font-size:11px; text-align:left;
    box-shadow:0 3px 12px rgba(0,0,0,0.5); max-width:200px;">
    <b style="color:#ffd740; font-size:12px;">Panduan Peta</b><br>
    <span style="color:#888;">&#x25B6;</span>
    Ikon <b style="color:white;">&#9776;</b> (kanan atas) = ganti layer<br>
    <span style="color:#888;">&#x25B6;</span> Hover zona = nama &amp; info singkat<br>
    <span style="color:#888;">&#x25B6;</span> Klik zona = statistik lengkap<br>
    <span style="color:#888;">&#x25B6;</span> Scroll = zoom in/out
</div>
"""

m.get_root().html.add_child(folium.Element(title_html))
m.get_root().html.add_child(folium.Element(legend_html))
m.get_root().html.add_child(folium.Element(hint_html))

output = Path("explore_map.html")
m.save(str(output))
print(f"[DONE] Map saved to {output.absolute()}")
print("       Buka explore_map.html di browser untuk melihat peta interaktif.")
