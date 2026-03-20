from oggm.shop import millan22


def add_velocity_data(gdirs):

    for gdir in gdirs:
        try:
            millan22.velocity_to_gdir(gdir)
        except Exception as e:
            print(f"Error occurred while processing {gdir.rgi_id}: {e}")


def get_velocity_statistics(gdirs):

    gdf_vel = millan22.compile_millan_statistics(gdirs)
    return gdf_vel
