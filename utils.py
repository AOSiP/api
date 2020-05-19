def get_date_from_zip(zip_name: str) -> str:
    """
      Helper function to parse a date from a ROM zip's name
    """
    return zip_name.replace('.zip', '').split("-")[4]


def get_metadata_from_zip(zip_name: str) -> (str, str, str, str):
    """
      Helper function to parse some data from ROM zip's name
    """
    data = zip_name.replace(".zip", "").split("-")
    return data[1], data[2], data[3], data[4]
