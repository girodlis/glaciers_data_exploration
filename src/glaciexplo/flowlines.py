def get_flowlines(gdir):
    """Extracts the flowlines from a glacier directory."""

    return gdir.read_pickle("model_flowlines")
