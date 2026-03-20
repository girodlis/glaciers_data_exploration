import folium
import matplotlib.pyplot as plt
import numpy as np
from src.utils import get_flowlines


def glaciers_location(gdf):
    """Create an interactive map of glaciers using Folium."""

    # Calculate the mean latitude and longitude for centering the map
    mean_lat = gdf["CenLat"].mean()
    mean_lon = gdf["CenLon"].mean()

    # Create a Folium map centered on the mean location
    glacier_map = folium.Map(location=[mean_lat, mean_lon], zoom_start=6)

    # Add markers for each glacier
    for _, row in gdf.iterrows():
        folium.Marker(
            location=[row["CenLat"], row["CenLon"]],
            tooltip=f"RGI ID: {row['RGIId']}<br>Slope: {row['Slope']:.2f}<br>Area: {row['Area']:.2f}",
        ).add_to(glacier_map)

    return glacier_map


def plot_flowline(gdir, bed=True, surface=True):
    """
    Plot the flowline of a glacier.

    """

    fls_cl = get_flowlines(gdir)
    cls = fls_cl[-1]
    np.asarray(cls.bed_h)
    x = np.arange(cls.nx) * cls.dx * cls.map_dx

    fig, ax = plt.subplots(figsize=(10, 6))
    if bed:
        ax.plot(
            x, cls.bed_h, color="0.35", linewidth=1.4, alpha=0.9, label="Bed elevation"
        )
    if surface:
        ax.plot(
            x,
            cls.surface_h,
            color="0.15",
            linewidth=1.4,
            alpha=0.9,
            label="Surface elevation",
        )
    ax.set_xlabel("Distance along flowline (m)")
    ax.set_ylabel("Elevation (m)")
    ax.set_title(f"Flowline of Glacier {gdir.rgi_id}")
    ax.grid(alpha=0.25, linestyle="--")
    ax.legend(loc="best")
    fig.tight_layout()
    plt.show()


def plot_flowline_slope(gdir, bed=True, surface=True):
    """
    Plot the slope of the flowline of a glacier.

    """

    fls_cl = get_flowlines(gdir)
    cls = fls_cl[-1]
    np.asarray(cls.bed_h)
    x = np.arange(cls.nx) * cls.dx * cls.map_dx

    bed_slope_deg = np.degrees(np.arctan(-np.gradient(cls.bed_h, x)))

    fig, ax = plt.subplots(figsize=(10, 6))
    if bed:
        ax.plot(
            x, cls.bed_h, color="0.35", linewidth=1.4, alpha=0.9, label="Bed elevation"
        )
    if surface:
        ax.plot(
            x,
            cls.surface_h,
            color="0.15",
            linewidth=1.4,
            alpha=0.9,
            label="Surface elevation",
        )

    sc = ax.scatter(
        x,
        cls.bed_h,
        c=bed_slope_deg,
        cmap="RdYlGn_r",
        s=24,
        edgecolor="none",
        label="Local slope color",
    )

    cbar = fig.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label("Bed slope (deg)")

    ax.set_xlabel("Distance along flowline (m)")
    ax.set_ylabel("Elevation (m)")
    ax.set_title(f"Slope of Flowline of Glacier {gdir.rgi_id}")
    ax.grid(alpha=0.25, linestyle="--")
    ax.legend(loc="best")
    fig.tight_layout()
    plt.show()
