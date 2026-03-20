import oggm
from pathlib import Path
import geopandas as gpd
from oggm import cfg, utils, workflow
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------
# Test


def get_oggm_version():
    """Returns the version of OGGM being used."""
    return oggm.__version__


# ----------------------------------------------------------
# Lets go


def setup_oggm_env(workspace_path="c", rgi_version="62", use_mp=True):
    """
    Configure the global OGGM environment and working directory.
    Run this once at the start of your script.
    """
    path_map = {"c": Path.cwd() / "OGGM_data", "p": Path.cwd().parent / "OGGM_data"}
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
    """Fetch and load RGI glacier outlines for a specific region."""

    rgi_path = utils.get_rgi_region_file(region, version=version)

    return gpd.read_file(rgi_path)


def filter_slope_area(gdf, slope_threshold=20, area_threshold=2):
    """Filter glaciers based on slope and area thresholds."""

    filtered_gdf = gdf[
        (gdf["Slope"] < slope_threshold) & (gdf["Area"] > area_threshold)
    ]
    logger.info(f"Filtered GDF: {len(filtered_gdf)} glaciers meet the criteria.")
    return filtered_gdf


def process_glacier_directories(gdf, prepro_level=3, prepro_border=80, reset=True):
    """
    Initializes glacier directories from preprocessed data.
    """
    # Safety Check
    MAX_GLACIERS = 300
    if len(gdf) > MAX_GLACIERS:
        raise ValueError(
            f"GDF length ({len(gdf)}) exceeds safety limit of {MAX_GLACIERS}."
        )

    base_url = "https://cluster.klima.uni-bremen.de/~oggm/gdirs/oggm_v1.6/L3-L5_files/2023.3/centerlines/W5E5/"

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


def get_flowlines(gdir):
    """Extracts the flowlines from a glacier directory."""
    return gdir.read_pickle("model_flowlines")
