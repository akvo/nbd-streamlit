import streamlit as st

st.set_page_config(
    page_title="River Basin Explorer",
    page_icon="🌍",
    layout="wide"
)

st.title("River Basin Explorer")
st.subheader("Interactive Visualizations and  Land Use Change explorer")

st.markdown('#### [How to Use](https://www.loom.com/share/9a562bd1b57b47319473a1446b35626d)')

st.markdown("""
This application provides interactive visualizations of river basins in the Mara region,
showing land use change analysis, terrain, and environmental data.

### Available Basins

Select a basin from the sidebar to explore:

- **Mara Basin** - Full Mara River basin spanning Kenya and Tanzania
- **Lower Mara Basin** - Lower section of the Mara River basin

### Visualizations

Each basin page includes:
- **3D Visualization** - Interactive terrain with population, altitude, slope, and rainfall layers
- **Land Cover Change** - Before/after comparison of land use (2017 vs 2024)

---

*Use the sidebar to navigate between basins.*
""")

# Footer
st.markdown("---")
st.caption("Data sources: Google Earth Engine, WorldPop, CHIRPS, Dynamic World")
