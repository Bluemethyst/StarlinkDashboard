import starlink_grpc, json, png

DEFAULT_OBSTRUCTED_COLOR = "FFED524A"
DEFAULT_UNOBSTRUCTED_COLOR = "FF3E80E0"
DEFAULT_NO_DATA_COLOR = "00000000"

def fetch_current_data():
    """
    Fetch the current data from the Starlink dish.

    Returns a JSON representation of the current data.
    """
    data = starlink_grpc.status_data()
    return json.dumps(data[0])

def get_starlink_model():
    """
    Get the model of the Starlink dish.

    Returns a JSON representation of the dish model. If the hardware version is
    "rev3_proto2", it will return "Standard Actuated". Otherwise, it will return
    the hardware version as returned by the Starlink API.
    """
    
    data = starlink_grpc.status_data()
    if data[0]["hardware_version"] == "rev3_proto2":
        dishy_model = "Standard Actuated"
    else:
        dishy_model = data[0]["hardware_version"]
         
    full_data = {"dishy_model": dishy_model}
    return full_data
    


def generate_obstruction_map_png(
    snr_data,
    filename="obstruction_map.png",
    obstructed_color=DEFAULT_OBSTRUCTED_COLOR,
    unobstructed_color=DEFAULT_UNOBSTRUCTED_COLOR,
    no_data_color=DEFAULT_NO_DATA_COLOR,
    greyscale=False,
    no_alpha=False,
):
    """
    Generate a PNG image from a Starlink obstruction map.

    Parameters:

    * snr_data: A 2D array of numbers between 0 and 1, where 0 means the
      point is obstructed and 1 means it is not.
    * filename: The filename to write to.
    * obstructed_color: The color to use for obstructed points. A 6-digit
      hex color code.
    * unobstructed_color: The color to use for unobstructed points. A 6-digit
      hex color code.
    * no_data_color: The color to use for points with no data. A 6-digit
      hex color code.
    * greyscale: If True, generate a greyscale image instead of an RGB
      image.
    * no_alpha: If True, generate a image without an alpha channel.

    Raises a ValueError if the input data is invalid (i.e. zero-length).

    Returns nothing.
    """    
    def hex_to_rgba(hex_color, greyscale=False):
        color = int(hex_color, 16)
        if greyscale:
            return ((color >> 8) & 255, color & 255)
        else:
            return (
                (color >> 24) & 255,
                (color >> 16) & 255,
                (color >> 8) & 255,
                color & 255,
            )

    obstructed_rgba = hex_to_rgba(obstructed_color, greyscale)
    unobstructed_rgba = hex_to_rgba(unobstructed_color, greyscale)
    no_data_rgba = hex_to_rgba(no_data_color, greyscale)

    def pixel_bytes(row):
        for point in row:
            if point > 1.0:
                point = 1.0
            if point >= 0.0:
                if greyscale:
                    yield round(
                        point * unobstructed_rgba[1]
                        + (1.0 - point) * obstructed_rgba[1]
                    )
                else:
                    yield round(
                        point * unobstructed_rgba[1]
                        + (1.0 - point) * obstructed_rgba[1]
                    )
                    yield round(
                        point * unobstructed_rgba[2]
                        + (1.0 - point) * obstructed_rgba[2]
                    )
                    yield round(
                        point * unobstructed_rgba[3]
                        + (1.0 - point) * obstructed_rgba[3]
                    )
                if not no_alpha:
                    yield round(
                        point * unobstructed_rgba[0]
                        + (1.0 - point) * obstructed_rgba[0]
                    )
            else:
                if greyscale:
                    yield no_data_rgba[1]
                else:
                    yield no_data_rgba[1]
                    yield no_data_rgba[2]
                    yield no_data_rgba[3]
                if not no_alpha:
                    yield no_data_rgba[0]

    if not snr_data or not snr_data[0]:
        raise ValueError("Invalid SNR map data: Zero-length")

    with open(filename, "wb") as out_file:
        writer = png.Writer(
            len(snr_data[0]), len(snr_data), alpha=(not no_alpha), greyscale=greyscale
        )
        writer.write(out_file, (bytes(pixel_bytes(row)) for row in snr_data))

def generate_obstruction_map_svg(
    snr_data,
    filename="obstruction_map.svg",
    obstructed_color=DEFAULT_OBSTRUCTED_COLOR,
    unobstructed_color=DEFAULT_UNOBSTRUCTED_COLOR,
    no_data_color=DEFAULT_NO_DATA_COLOR,
    greyscale=False,
    upscale_factor=4 
):
    """
    Generate an SVG image from a Starlink obstruction map.

    Parameters:

    * snr_data: A 2D array of numbers between 0 and 1, where 0 means the
      point is obstructed and 1 means it is not.
    * filename: The filename to write to.
    * obstructed_color: The color to use for obstructed points. A 6-digit
      hex color code.
    * unobstructed_color: The color to use for unobstructed points. A 6-digit
      hex color code.
    * no_data_color: The color to use for points with no data. A 6-digit
      hex color code.
    * greyscale: If True, generate a greyscale image instead of an RGB
      image.
    * upscale_factor: A factor to scale the image up by. This can make the
      resulting image larger and more detailed, but it will also make it
      take longer to generate and will use more memory.

    Raises a ValueError if the input data is invalid (i.e. zero-length).

    Returns nothing.
    """
    def hex_to_rgb(hex_color):
        """Convert a hex color to an RGB tuple."""
        color = int(hex_color, 16)
        return (
            (color >> 16) & 255,
            (color >> 8) & 255,
            color & 255
        )

    obstructed_rgb = hex_to_rgb(obstructed_color)
    unobstructed_rgb = hex_to_rgb(unobstructed_color)
    no_data_rgb = hex_to_rgb(no_data_color)

    if not snr_data or not snr_data[0]:
        raise ValueError("Invalid SNR map data: Zero-length")

    width = len(snr_data[0]) * upscale_factor
    height = len(snr_data) * upscale_factor
    svg_content = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']

    for y, row in enumerate(snr_data):
        for x, point in enumerate(row):
            color = no_data_rgb
            if point >= 1.0:
                point = 1.0
            if point >= 0.0:
                color = (
                    round(point * unobstructed_rgb[0] + (1.0 - point) * obstructed_rgb[0]),
                    round(point * unobstructed_rgb[1] + (1.0 - point) * obstructed_rgb[1]),
                    round(point * unobstructed_rgb[2] + (1.0 - point) * obstructed_rgb[2]),
                )
                fill_color = f"rgb({color[0]},{color[1]},{color[2]})"
            else:
                fill_color = None
            svg_content.append(f'<rect x="{x * upscale_factor}" y="{y * upscale_factor}" width="{upscale_factor}" height="{upscale_factor}" fill="{fill_color}" shape-rendering="crispEdges"/>')

    svg_content.append('</svg>')

    with open(filename, "w") as out_file:
        out_file.write("\n".join(svg_content))

