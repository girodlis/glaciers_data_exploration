from oggm.shop import glathida


def add_thickness_data(gdirs):

    for gdir in gdirs:
        glathida.glathida_to_gdir(gdir)


def get_thickness_statistics(gdirs):

    gdf_thick = glathida.compile_glathida_statistics(gdirs)
    return gdf_thick
