"""
Generate split_map.html for Mara Basin using base64 imageOverlay (Sio strategy).
Reads landcover TIF files, converts to colored PNGs, embeds in Folium map.
"""
import io, base64, os
import numpy as np
import rasterio
import geopandas as gpd
import folium
from folium.elements import Element
from PIL import Image

INPUT_DIR = "Mara/input"
OUTPUT_HTML = "../data/mara_basin/split_map.html"

YEAR_1 = 2015
YEAR_2 = 2025
ZOOM = 9
BASIN_COLOR = "#000000"
RIVER_COLOR = "#0000CD"

DW_COLORS = {
    0: [65, 155, 223],
    1: [57, 125, 73],
    2: [136, 176, 83],
    3: [122, 135, 198],
    4: [228, 150, 53],
    5: [223, 195, 90],
    6: [196, 40, 27],
    7: [165, 155, 143],
    8: [179, 159, 225],
}

def raster_to_colored_png(lc_data, dw_colors, nodata_val=255):
    h, w = lc_data.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    for class_id, rgb in dw_colors.items():
        mask = lc_data == class_id
        rgba[mask, 0] = rgb[0]
        rgba[mask, 1] = rgb[1]
        rgba[mask, 2] = rgb[2]
        rgba[mask, 3] = 255
    rgba[lc_data == nodata_val, 3] = 0
    return Image.fromarray(rgba, "RGBA")

def png_to_data_uri(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"

# Read landcover TIFs
print("Reading landcover rasters...")
tif_2015 = os.path.join(INPUT_DIR, "landcover_2015.tif")
tif_2025 = os.path.join(INPUT_DIR, "landcover_2025.tif")

with rasterio.open(tif_2015) as src:
    lc_2015 = src.read(1)
    bounds = src.bounds
    min_lon, min_lat, max_lon, max_lat = bounds.left, bounds.bottom, bounds.right, bounds.top
    print(f"  2015 shape: {lc_2015.shape}, bounds: [{min_lat:.4f}, {min_lon:.4f}] to [{max_lat:.4f}, {max_lon:.4f}]")

with rasterio.open(tif_2025) as src:
    lc_2025 = src.read(1)
    print(f"  2025 shape: {lc_2025.shape}")

print(f"  2015 unique classes: {np.unique(lc_2015)}")
print(f"  2025 unique classes: {np.unique(lc_2025)}")

# Generate colored PNGs
print("Generating colored PNGs...")
img_2015 = raster_to_colored_png(lc_2015, DW_COLORS)
img_2025 = raster_to_colored_png(lc_2025, DW_COLORS)

lc_uri_2015 = png_to_data_uri(img_2015)
lc_uri_2025 = png_to_data_uri(img_2025)
print(f"  Base64 sizes: {len(lc_uri_2015)//1024} KB, {len(lc_uri_2025)//1024} KB")

# Map center
center_lat = (min_lat + max_lat) / 2
center_lon = (min_lon + max_lon) / 2
print(f"  Center: [{center_lat:.4f}, {center_lon:.4f}]")

# Create folium map
basemap_url = "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=ZOOM,
    tiles=None,
    zoom_control=True,
    dragging=True,
    scrollWheelZoom=True,
)
m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

folium.TileLayer(tiles=basemap_url, attr="Google Satellite Hybrid", name="Satellite Hybrid").add_to(m)

img_bounds = [[min_lat, min_lon], [max_lat, max_lon]]

left_overlay = folium.raster_layers.ImageOverlay(
    image=lc_uri_2015, bounds=img_bounds,
    name=f"Land Cover {YEAR_1}", opacity=1.0, interactive=False
)
left_overlay.add_to(m)

right_overlay = folium.raster_layers.ImageOverlay(
    image=lc_uri_2025, bounds=img_bounds,
    name=f"Land Cover {YEAR_2}", opacity=1.0, interactive=False
)
right_overlay.add_to(m)

# Add basin boundary
print("Loading shapefiles...")
basin_gdf = gpd.read_file(os.path.join(INPUT_DIR, "basin.shp"))
basin_geojson = basin_gdf.__geo_interface__
folium.GeoJson(
    basin_geojson, name="Basin Boundary",
    style_function=lambda x: {"color": BASIN_COLOR, "weight": 2, "fillOpacity": 0}
).add_to(m)

# Add river
river_gdf = gpd.read_file(os.path.join(INPUT_DIR, "mara-river.shp"))
river_geojson = river_gdf.__geo_interface__
folium.GeoJson(
    river_geojson, name="River",
    style_function=lambda x: {"color": RIVER_COLOR, "weight": 2}
).add_to(m)

# Split slider JS (CSS clip-path approach, works with ImageOverlay)
split_slider_js = """
<style>
#split-slider {
    position: absolute;
    top: 0; bottom: 0;
    width: 4px;
    background: white;
    left: 50%;
    z-index: 999;
    cursor: ew-resize;
    box-shadow: 0 0 6px rgba(0,0,0,0.5);
}
#split-handle {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 36px; height: 36px;
    background: white;
    border-radius: 50%;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; color: #555;
    user-select: none;
    pointer-events: none;
}
</style>

<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var mapContainer = document.querySelector('.folium-map');
        if (!mapContainer) return;

        var slider = document.createElement('div');
        slider.id = 'split-slider';
        var handle = document.createElement('div');
        handle.id = 'split-handle';
        handle.innerHTML = '&#x2194;';
        slider.appendChild(handle);
        mapContainer.style.position = 'relative';
        mapContainer.appendChild(slider);

        function getImages() {
            return mapContainer.querySelectorAll('.leaflet-image-layer');
        }

        function updateClip(xPct) {
            slider.style.left = xPct + '%';
            var containerRect = mapContainer.getBoundingClientRect();
            var splitX = containerRect.left + (xPct / 100) * containerRect.width;
            var images = getImages();
            var leftImg = images.length >= 2 ? images[0] : null;
            var rightImg = images.length >= 2 ? images[1] : null;
            if (leftImg) {
                var r = leftImg.getBoundingClientRect();
                var clipRight = Math.max(0, Math.min(100, ((r.right - splitX) / r.width) * 100));
                leftImg.style.clipPath = 'inset(0 ' + clipRight + '% 0 0)';
            }
            if (rightImg) {
                var r = rightImg.getBoundingClientRect();
                var clipLeft = Math.max(0, Math.min(100, ((splitX - r.left) / r.width) * 100));
                rightImg.style.clipPath = 'inset(0 0 0 ' + clipLeft + '%)';
            }
        }
        updateClip(50);

        var dragging = false;
        slider.addEventListener('mousedown', function(e) { dragging = true; e.preventDefault(); });
        slider.addEventListener('touchstart', function(e) { dragging = true; });
        document.addEventListener('mouseup', function() { dragging = false; });
        document.addEventListener('touchend', function() { dragging = false; });

        function onMove(clientX) {
            if (!dragging) return;
            var rect = mapContainer.getBoundingClientRect();
            var x = clientX - rect.left;
            var pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
            updateClip(pct);
        }
        document.addEventListener('mousemove', function(e) { onMove(e.clientX); });
        document.addEventListener('touchmove', function(e) { onMove(e.touches[0].clientX); });
    }, 500);
});
</script>
"""

legend_html = """
<div style="position: fixed; bottom: 20px; right: 10px; z-index: 1000;
            background: rgba(0,0,0,0.85); padding: 12px 16px; border-radius: 8px;
            color: white; font-family: -apple-system, sans-serif; font-size: 12px;">
    <h4 style="margin: 0 0 10px 0; font-size: 13px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 6px;">Land Cover Classes</h4>
    <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 20px; height: 14px; background: #419BDF; margin-right: 8px; border-radius: 2px;"></div>Water</div>
    <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 20px; height: 14px; background: #397D49; margin-right: 8px; border-radius: 2px;"></div>Trees</div>
    <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 20px; height: 14px; background: #88B053; margin-right: 8px; border-radius: 2px;"></div>Grass</div>
    <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 20px; height: 14px; background: #7A87C6; margin-right: 8px; border-radius: 2px;"></div>Flooded Vegetation</div>
    <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 20px; height: 14px; background: #E49635; margin-right: 8px; border-radius: 2px;"></div>Crops</div>
    <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 20px; height: 14px; background: #DFC35A; margin-right: 8px; border-radius: 2px;"></div>Shrub & Scrub</div>
    <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 20px; height: 14px; background: #C4281B; margin-right: 8px; border-radius: 2px;"></div>Built Area</div>
    <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 20px; height: 14px; background: #A59B8F; margin-right: 8px; border-radius: 2px;"></div>Bare Ground</div>
    <div style="display: flex; align-items: center;"><div style="width: 20px; height: 14px; background: #B39FE1; margin-right: 8px; border-radius: 2px;"></div>Snow & Ice</div>
</div>
"""

year_labels_html = f"""
<div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); z-index: 1000;
            background: rgba(0,0,0,0.85); padding: 12px 24px; border-radius: 8px;
            color: white; font-family: -apple-system, sans-serif; font-size: 14px;
            display: flex; gap: 40px;">
    <span style="font-weight: 600; color: #f6ad55;">{YEAR_1}</span>
    <span style="color: rgba(255,255,255,0.5);">|</span>
    <span style="font-weight: 600; color: #68d391;">{YEAR_2}</span>
</div>
"""

ref_legend_html = f"""
<div style="position: fixed; bottom: 20px; left: 10px; z-index: 1000;
            background: rgba(0,0,0,0.85); padding: 10px 14px; border-radius: 8px;
            color: white; font-family: -apple-system, sans-serif; font-size: 12px;">
    <h4 style="margin: 0 0 8px 0; font-size: 12px;">Reference</h4>
    <div style="display: flex; align-items: center; margin-bottom: 4px;"><div style="width: 24px; height: 3px; background: {BASIN_COLOR}; margin-right: 8px;"></div>Basin Boundary</div>
    <div style="display: flex; align-items: center;"><div style="width: 24px; height: 3px; background: {RIVER_COLOR}; margin-right: 8px;"></div>River</div>
</div>
"""

toggle_html = """
<div id="layer-toggle" style="position: fixed; top: 60px; right: 10px; z-index: 1000;
            background: rgba(0,0,0,0.85); padding: 10px 14px; border-radius: 8px;
            color: white; font-family: -apple-system, sans-serif; font-size: 12px;">
    <h4 style="margin: 0 0 8px 0; font-size: 12px;">Layer Controls</h4>
    <label style="display: flex; align-items: center; cursor: pointer; margin-bottom: 6px;">
        <input type="checkbox" id="toggle-landcover" checked style="margin-right: 8px;">
        Show Land Cover
    </label>
    <div style="font-size: 10px; color: rgba(255,255,255,0.6); margin-top: 4px;">
        Uncheck to see satellite only
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    var checkbox = document.getElementById('toggle-landcover');
    function setLandCoverOpacity(opacity) {
        var overlays = document.querySelectorAll('.leaflet-image-layer');
        var slider = document.getElementById('split-slider');
        for (var i = 0; i < overlays.length; i++) {
            overlays[i].style.opacity = opacity;
        }
        if (slider) slider.style.display = opacity > 0 ? 'block' : 'none';
    }
    checkbox.addEventListener('change', function() {
        setLandCoverOpacity(this.checked ? 1 : 0);
    });
});
</script>
"""

m.get_root().html.add_child(Element(split_slider_js))
m.get_root().html.add_child(Element(legend_html))
m.get_root().html.add_child(Element(year_labels_html))
m.get_root().html.add_child(Element(ref_legend_html))
m.get_root().html.add_child(Element(toggle_html))

# Save HTML
html_file = OUTPUT_HTML
m.save(html_file)

# Inject fitBounds fix for Streamlit iframe
map_name = m.get_name()
fit_fix_js = f"""
    (function() {{
        var m = {map_name};
        var bounds = [[{min_lat}, {min_lon}], [{max_lat}, {max_lon}]];
        function refitMap() {{
            m.invalidateSize();
            m.fitBounds(bounds);
        }}
        setTimeout(refitMap, 100);
        setTimeout(refitMap, 500);
        setTimeout(refitMap, 1500);
        if (typeof ResizeObserver !== 'undefined') {{
            var ro = new ResizeObserver(function() {{ refitMap(); }});
            ro.observe(m.getContainer());
        }}
    }})();
"""
with open(html_file, "r") as f:
    html_content = f.read()
html_content = html_content.replace("</script>\n</html>", fit_fix_js + "</script>\n</html>")
with open(html_file, "w") as f:
    f.write(html_content)

print(f"\nSaved: {html_file}")
print("Land cover embedded as base64 PNG — works in Streamlit iframes.")
