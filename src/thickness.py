from oggm.shop import glathida
from oggm.core import gis

import pandas as pd
import numpy as np


def add_thickness_data(gdirs):

    for gdir in gdirs:
        glathida.glathida_to_gdir(gdir)


def get_thickness_statistics(gdirs):

    gdf_thick = glathida.compile_glathida_statistics(gdirs)
    return gdf_thick


def glacier_thickness_coverage(gdir):
    """
    Calculate the percentage and number of grid points of the glacier area covered by thickness data.

    Args:
        gdir: Glacier directory.

    Returns:
        float: Percentage of the glacier area covered by thickness data.
        int: Number of grid points with thickness data.
    """

    try:
        df_gtd = pd.read_csv(gdir.get_filepath("glathida_data"))
        n_ij_grid = df_gtd["ij_grid"].nunique()
        dem = gis.read_geotiff_dem(gdir)
        total_pixels = dem.shape[0] * dem.shape[1]
        percentage = n_ij_grid / total_pixels * 100
    except FileNotFoundError:
        # logging.warning(f"Thickness data not found for glacier {gdir.rgi_id}. Skipping.")
        percentage = np.nan
        n_ij_grid = np.nan

    return percentage, n_ij_grid


def create_df_thickness_coverage(gdirs):
    """
    Create a DataFrame with the thickness coverage for each glacier.

    Args:
        gdirs (list): List of glacier directories.

    Returns:
        pd.DataFrame: DataFrame with the thickness coverage for each glacier.
    """

    coverage_list = []
    for gdir in gdirs:
        percentage, n_ij_grid = glacier_thickness_coverage(gdir)
        coverage_list.append(
            {
                "RGIId": gdir.rgi_id,
                "thickness_coverage_percentage": percentage,
                "thickness_grid_points": n_ij_grid,
            }
        )

    df_thick_coverage = pd.DataFrame(coverage_list)
    return df_thick_coverage
