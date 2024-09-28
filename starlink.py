import starlink_grpc, json, png

from google.protobuf.json_format import MessageToDict

DEFAULT_OBSTRUCTED_COLOR = "FFED524A"
DEFAULT_UNOBSTRUCTED_COLOR = "FF3E80E0"
DEFAULT_NO_DATA_COLOR = "00000000"


def fetch_current_data():
    """
    Fetch the current data from the Starlink dish.

    Returns a JSON representation of the current data.
    """
    data = starlink_grpc.status_data()
    data2 = starlink_grpc.history_stats(-1)
    final = {
        "download_throughput_bps": data[0]["downlink_throughput_bps"],
        "upload_throughput_bps": data[0]["uplink_throughput_bps"],
        "ping_latency_ms": data[0]["pop_ping_latency_ms"],
        "power_usage_watts": data2[6]["latest_power"],
        "fraction_obstructed": data[0]["fraction_obstructed"],
        "state": data[0]["state"],
        "alerts": data[2],
    }
    return json.dumps(final)


def get_starlink_inital_data():
    """
    Get the model of the Starlink dish.

    Returns a JSON representation of the dish model. If the hardware version is
    "rev3_proto2", it will return "Standard Actuated". Otherwise, it will return
    the hardware version as returned by the Starlink API.
    """

    data = starlink_grpc.status_data()
    data2 = MessageToDict(starlink_grpc.get_status())
    if data[0]["hardware_version"] == "rev3_proto2":
        dishy_model = "Standard Actuated"
    else:
        dishy_model = data[0]["hardware_version"]

    full_data = {
        "dishy_model": dishy_model,
        "country_code": data2["deviceInfo"]["countryCode"],
    }
    return full_data


def generate_obstruction_map_svg(
    snr_data,
    filename="obstruction_map.svg",
    obstructed_color=DEFAULT_OBSTRUCTED_COLOR,
    unobstructed_color=DEFAULT_UNOBSTRUCTED_COLOR,
    no_data_color=DEFAULT_NO_DATA_COLOR,
    upscale_factor=4,
    font="D-DIN",
    font_size=40,
):
    """
    Generate an SVG image from a Starlink obstruction map with compass directions.
    """

    def hex_to_rgb(hex_color):
        """Convert a hex color to an RGB tuple."""
        color = int(hex_color, 16)
        return ((color >> 16) & 255, (color >> 8) & 255, color & 255)

    obstructed_rgb = hex_to_rgb(obstructed_color)
    unobstructed_rgb = hex_to_rgb(unobstructed_color)
    no_data_rgb = hex_to_rgb(no_data_color)

    if not snr_data or not snr_data[0]:
        raise ValueError("Invalid SNR map data: Zero-length")

    width = len(snr_data[0]) * upscale_factor
    height = len(snr_data) * upscale_factor
    svg_content = [
        f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
        f"<style>text {{ font-family: {font}; font-size: {font_size}px; color: #FFFFFF; }}</style>",
    ]

    # Generate the obstruction map
    for y, row in enumerate(snr_data):
        for x, point in enumerate(row):
            color = no_data_rgb
            if point >= 1.0:
                point = 1.0
            if point >= 0.0:
                color = (
                    round(
                        point * unobstructed_rgb[0] + (1.0 - point) * obstructed_rgb[0]
                    ),
                    round(
                        point * unobstructed_rgb[1] + (1.0 - point) * obstructed_rgb[1]
                    ),
                    round(
                        point * unobstructed_rgb[2] + (1.0 - point) * obstructed_rgb[2]
                    ),
                )
                fill_color = f"rgb({color[0]},{color[1]},{color[2]})"
            else:
                fill_color = None
            svg_content.append(
                f'<rect x="{x * upscale_factor}" y="{y * upscale_factor}" width="{upscale_factor}" height="{upscale_factor}" fill="{fill_color}" shape-rendering="crispEdges"/>'
            )

    # Add compass lettering (N, S, E, W)
    svg_content.append(
        f'<text x="{width / 2}" y="{font_size}" text-anchor="middle" fill="white">N</text>'
    )  # North
    svg_content.append(
        f'<text x="{width / 2}" y="{height - font_size / 2}" text-anchor="middle" fill="white">S</text>'
    )  # South
    svg_content.append(
        f'<text x="{font_size / 2}" y="{height / 2}" text-anchor="middle" fill="white">W</text>'
    )  # West
    svg_content.append(
        f'<text x="{width - font_size / 2}" y="{height / 2}" text-anchor="middle" fill="white">E</text>'
    )  # East

    svg_content.append("</svg>")

    with open(filename, "w") as out_file:
        out_file.write("\n".join(svg_content))
