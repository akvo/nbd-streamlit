import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Mara Basin",
    page_icon="🏞️",
    layout="wide"
)

# Data folder path
DATA_DIR = Path(__file__).parent.parent / "data" / "mara_basin"

def load_html(file_path):
    """Load HTML content from file."""
    if file_path.exists():
        return file_path.read_text(encoding='utf-8')
    else:
        return None

st.title("Mara Basin")
st.markdown("*Trans-boundary river basin spanning Kenya and Tanzania*")
st.markdown('#### Basin Area : 13571 sq km')

# Create tabs
tab1, tab2 = st.tabs(["3D Visualization", "Land Cover Change"])

with tab1:
    html_file = DATA_DIR / "3d_visualization.html"
    html_content = load_html(html_file)

    if html_content:
        components.html(html_content, height=750, scrolling=True)
    else:
        st.warning(f"3D visualization not found. Please add `3d_visualization.html` to `data/mara_basin/`")
        st.info("Expected path: " + str(html_file))

with tab2:
    html_file = DATA_DIR / "split_map.html"
    html_content = load_html(html_file)

    if html_content:
        components.html(html_content, height=650, scrolling=True)
    else:
        st.warning(f"Split map not found. Please add `split_map.html` to `data/mara_basin/`")
        st.info("Expected path: " + str(html_file))

    # Land Use Change Summary Table
    summary_file = DATA_DIR / "landuse_change_summary.csv"
    if summary_file.exists():
        st.subheader("Land Use Change Summary (2015-2025)")
        df_summary = pd.read_csv(summary_file)
        df_display = df_summary[['Class Name', 'Area 2015 (sq km)', 'Area 2025 (sq km)', 'Change (sq km)', 'Change (%)']].copy()
        df_display.columns = ['Land Cover Class', 'Area 2015 (km²)', 'Area 2025 (km²)', 'Change (km²)', 'Change (%)']
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Sankey Diagram from Transition Matrix
    transition_file = DATA_DIR / "transition_matrix.csv"
    if transition_file.exists():
        st.subheader("Land Cover Transitions (2015 → 2025)")
        df_transition = pd.read_csv(transition_file, index_col=0)

        # Prepare data for Sankey
        source_labels = [f"{name} (2015)" for name in df_transition.index]
        target_labels = [f"{name} (2025)" for name in df_transition.columns]
        all_labels = source_labels + target_labels

        source_indices = []
        target_indices = []
        values = []

        for i, source in enumerate(df_transition.index):
            for j, target in enumerate(df_transition.columns):
                value = df_transition.loc[source, target]
                if value > 0:
                    source_indices.append(i)
                    target_indices.append(len(source_labels) + j)
                    values.append(value)

        # Color mapping for land cover classes
        colors = {
            'Water': '#419bdf',
            'Trees': '#397d49',
            'Grass': '#88b053',
            'Flooded Vegetation': '#7a87c6',
            'Crops': '#e49635',
            'Shrub & Scrub': '#dfc35a',
            'Built Area': '#c4281b',
            'Bare Ground': '#a59b8f',
            'Snow & Ice': '#b39fe1'
        }

        node_colors = [colors.get(name, '#888888') for name in df_transition.index] + \
                      [colors.get(name, '#888888') for name in df_transition.columns]

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_labels,
                color=node_colors
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values
            )
        )])

        fig.update_layout(
            font=dict(size=16, color='black', family='Arial Black'),
            height=700,
            margin=dict(l=20, r=20, t=20, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)
