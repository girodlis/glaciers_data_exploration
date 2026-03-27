import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from glaciexplo import utils, slope, thickness, velocity


def glaciers_location(gdf, outlines=False):
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
            tooltip=f"RGI ID: {row['RGIId']}<br>Mean slope: {row['Slope']:.2f}°<br>Area: {row['Area']:.2f}km2",
        ).add_to(glacier_map)
        if outlines:
            folium.GeoJson(
                data=gdf.geometry,
                name="Glacier Outlines",
                style_function=lambda x: {
                    "fillColor": "#00ffff",
                    "color": "black",
                    "weight": 1,
                    "fillOpacity": 0.5,
                },
            ).add_to(glacier_map)

    return glacier_map


def plot_dem_slope(gdir, ax=None):
    """Plot the slope of the DEM for a glacier."""

    ds = utils.get_ds(gdir)
    slope_masked = slope.get_dem_slope(gdir)

    smap = ds.salem.get_map(countries=False)
    smap.set_shapefile(gdir.read_shapefile("outlines"))
    smap.set_topography(ds.topo.data)

    created_fig = False
    if ax is None:
        f, ax = plt.subplots(figsize=(9, 9))
        created_fig = True

    smap.set_cmap("viridis")
    smap.set_data(slope_masked)
    smap.plot(ax=ax)
    smap.append_colorbar(ax=ax, label="Slope (degrees)")

    ax.set_title(f"Slope on the full glacier {gdir.rgi_id}")
    if created_fig:
        plt.show()


def plot_thickness_coverage(gdir, ax=None):
    """
    Plot the thickness data from GlaThIDA for a glacier.

    Args:
        gdir: Glacier directory.

    Returns:
        None
    """

    geom = gdir.read_shapefile("outlines")
    df_gtd = pd.read_csv(gdir.get_filepath("glathida_data"))
    percentage, n_ij_grid = thickness.glacier_thickness_coverage(gdir)

    created_fig = False
    if ax is None:
        f, ax = plt.subplots(figsize=(9, 9))
        created_fig = True

    if ax is not None:
        s = 10
    else:
        s = 2

    df_gtd.plot.scatter(
        x="x_proj", y="y_proj", c="thickness", cmap="viridis", ax=ax, s=s
    )
    geom.plot(ax=ax, facecolor="none", edgecolor="k")

    if created_fig:
        plt.title(
            f"Glacier: {gdir.rgi_id} - Thickness Coverage: {percentage:.2f}% ({n_ij_grid} grid points)"
        )
        plt.xlabel("x_proj")
        plt.ylabel("y_proj")
        plt.show()


def plot_velocity(gdir, ax=None):
    """
    Plot the velocity data for a glacier.

    Args:
        gdir: Glacier directory.

    Returns:
        None
    """
    ds = utils.get_ds(gdir)
    # get the velocity data
    u = ds.millan_vx.where(ds.glacier_mask)
    v = ds.millan_vy.where(ds.glacier_mask)
    ws = ds.millan_v.where(ds.glacier_mask)

    smap = ds.salem.get_map(countries=False)
    smap.set_shapefile(gdir.read_shapefile("outlines"))
    smap.set_topography(ds.topo.data)

    # get the axes ready
    created_fig = False
    if ax is None:
        f, ax = plt.subplots(figsize=(9, 9))
        created_fig = True

    # Quiver only every N grid point
    us = u[1::3, 1::3]
    vs = v[1::3, 1::3]

    smap.set_data(ws)
    smap.set_cmap("Blues")
    smap.plot(ax=ax)
    smap.append_colorbar(ax=ax, label="ice velocity (m yr$^{-1}$)")

    # transform their coordinates to the map reference system and plot the arrows
    xx, yy = smap.grid.transform(us.x.values, us.y.values, crs=gdir.grid.proj)
    xx, yy = np.meshgrid(xx, yy)
    qu = ax.quiver(xx, yy, us.values, vs.values)
    ax.quiverkey(qu, 0.82, 0.97, 10, "10 m yr$^{-1}$", labelpos="E", coordinates="axes")
    ax.set_title("Millan 2022 velocity")
    if created_fig:
        plt.show()


def merge_glacier_data(gdirs, gdf, slope_threshold=20):
    """Generate a merged GeoDataFrame containing:
        - glacier information,
        - thickness coverage,
        - percentage of glacier surface with slope above threshold,
        - velocity errors for glaciers.

    Args:
        gdirs: list of GlacierDirectory objects.
        gdf: GeoDataFrame with glacier information (must contain 'RGIId' column).
        slope_threshold: slope threshold in degrees to calculate the percentage of glacier surface above it.

    Returns:
        GeoDataFrame.
    """
    data_thick = thickness.create_df_thickness_coverage(gdirs)
    data_vel = velocity.create_df_velocity_errors(gdirs)
    data_slope = slope.create_df_slope_above(gdirs, threshold=slope_threshold)

    # verify that the 'RGIId' column exists in all DataFrames
    for df in [gdf, data_thick, data_vel, data_slope]:
        if "RGIId" not in df.columns:
            raise ValueError(
                "All DataFrames must contain an 'RGIId' column for merging."
            )

    gdf_merged = gdf.merge(data_thick, on="RGIId", how="left")
    gdf_merged = gdf_merged.merge(data_slope, on="RGIId", how="left")
    gdf_merged = gdf_merged.merge(data_vel, on="RGIId", how="left")

    return gdf_merged
