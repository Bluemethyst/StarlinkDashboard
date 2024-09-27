import starlink_grpc, png, json
from spacex.starlink import StarlinkDish


dishy = StarlinkDish()
dishy.connect()

print(json.dumps(starlink_grpc.status_data(), indent=4))


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

