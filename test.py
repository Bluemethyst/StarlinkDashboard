import starlink_grpc, png, json

# print(json.dumps(starlink_grpc.status_data(), indent=4))
print(starlink_grpc.get_status())
# print(json.dumps(starlink_grpc.history_stats(-1), indent=4))


DEFAULT_OBSTRUCTED_COLOR = "FFED524A"
DEFAULT_UNOBSTRUCTED_COLOR = "FF3E80E0"
DEFAULT_NO_DATA_COLOR = "00000000"


def generate_obstruction_map_png(
    snr_data,
    filename="obstruction_map.png",
    obstructed_color=DEFAULT_OBSTRUCTED_COLOR,
    unobstructed_color=DEFAULT_UNOBSTRUCTED_COLOR,
    no_data_color=DEFAULT_NO_DATA_COLOR,
    greyscale=False,
    no_alpha=False,
):
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

    print(f"PNG file '{filename}' generated successfully.")


def generate_obstruction_map_svg(
    snr_data,
    filename="obstruction_map.svg",
    obstructed_color=DEFAULT_OBSTRUCTED_COLOR,
    unobstructed_color=DEFAULT_UNOBSTRUCTED_COLOR,
    no_data_color=DEFAULT_NO_DATA_COLOR,
    greyscale=False,
    upscale_factor=4,
    font="Arial",  # Add font parameter
    font_size=24,  # Add font size parameter
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
