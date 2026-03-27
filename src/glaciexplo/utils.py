import oggm
from oggm import cfg, utils, workflow

from pathlib import Path
import geopandas as gpd
import xarray as xr
import logging
import warnings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------
# Test


def get_oggm_version():
    """Returns the version of OGGM being used."""
    return oggm.__version__


# ----------------------------------------------------------
# Lets go


def setup_oggm_env(
    workspace_path="c", rgi_version="62", use_mp=True, folder_name="OGGM_data"
):
    """
    Configure the global OGGM environment and working directory.
    Run this once at the start of your script.

    Args:
        workspace_path (str): Path to the working directory. Use "c" for current directory, "p" for parent directory, or provide a custom path.
        rgi_version (str): RGI version to use (e.g., "62").
        use_mp (bool): Whether to use multiprocessing for OGGM tasks.
        folder_name (str): Name of the folder to create for OGGM data
    """
    path_map = {"c": Path.cwd() / folder_name, "p": Path.cwd().parent / folder_name}
    work_dir = path_map.get(workspace_path, Path(workspace_path))
    work_dir.mkdir(parents=True, exist_ok=True)

    # Global OGGM Config
    cfg.initialize(logging_level="WARNING")
    cfg.PARAMS["rgi_version"] = rgi_version
    cfg.PARAMS["use_multiprocessing"] = use_mp
    cfg.PATHS["working_dir"] = str(work_dir)

    logger.info(f"OGGM Initialized. Working directory: {work_dir}")
    return work_dir


def fetch_rgi_data(region, version="62"):
    """
    Fetch and load RGI glacier outlines for a specific region.

    Args:
        region (int): RGI region code (e.g., 11 for European Alps).
        version (str): RGI version to use (default is "62").

    Returns:
        GeoDataFrame: A GeoDataFrame containing the glacier outlines and some other information for the specified region.
    """

    rgi_path = utils.get_rgi_region_file(region, version=version)

    return gpd.read_file(rgi_path)


def filter_slope_area(gdf, slope_threshold, area_threshold):
    """
    Filter glaciers based on slope and area thresholds.

    Args:
        gdf (GeoDataFrame): Input GeoDataFrame with glacier data.
        slope_threshold (float): Minimum mean slope threshold in degrees.
        area_threshold (float): Minimum area threshold in square kilometers.

    Returns:
        GeoDataFrame: A filtered GeoDataFrame containing only glaciers that meet the slope and area criteria.
    """

    filtered_gdf = gdf[
        (gdf["Slope"] < slope_threshold) & (gdf["Area"] > area_threshold)
    ]
    logger.info(f"Filtered GDF: {len(filtered_gdf)} glaciers meet the criteria.")
    return filtered_gdf


def process_glacier_directories(
    gdf,
    prepro_level=3,
    prepro_border=80,
    reset=True,
    base_url="https://cluster.klima.uni-bremen.de/~oggm/gdirs/oggm_v1.6/L3-L5_files/2023.3/elev_bands/W5E5/",
):
    """
    Initializes glacier directories from preprocessed data.

    Args:
        gdf (GeoDataFrame): GeoDataFrame containing glacier information.
        prepro_level (int): Preprocessing level to use (default is 3).
        prepro_border (int): Border size for preprocessing (default is 80).
        reset (bool): Whether to reset existing glacier directories (default is True).
        base_url (str): Base URL where to found the preprocessed data.
    """
    # Safety Check
    if len(gdf) > 300:
        warnings.warn(f"The GDF contains {len(gdf)} elements. This may take some time.")
        response = input("Do you want to continue? (y/N) : ")
        if response.lower() not in ("y", "yes"):
            print("Operation cancelled by user.")
            return

    base_url = base_url

    try:
        gdirs = workflow.init_glacier_directories(
            gdf,
            from_prepro_level=prepro_level,
            prepro_base_url=base_url,
            reset=reset,
            prepro_border=prepro_border,
        )
        logger.info(f"Successfully initialized {len(gdirs)} glacier directories.")
        return gdirs
    except Exception as e:
        logger.error(f"Workflow initialization failed: {e}")
        raise


def get_ds(gdir):
    """Load the gridded dataset for a glacier directory."""
    with xr.open_dataset(gdir.get_filepath("gridded_data")) as ds:
        ds = ds.load()
    return ds


def find_gdir_index(gdirs, rgi_id):
    """Find the index of a glacier directory given its RGI ID."""
    for idx, gdir in enumerate(gdirs):
        if gdir.rgi_id == rgi_id:
            return idx
    raise ValueError(f"RGI ID {rgi_id} not found in glacier directories.")
