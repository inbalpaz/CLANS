from vispy import color


def generate_distinct_colors(colors_num):

    # Use fixed saturation and brightness
    s = 0.85
    v = 0.95

    # The interval between the hues
    interval = 360 / colors_num

    colors = []

    # Always start from red (hue = 0)
    h = 0.0

    for i in range(colors_num):

        hsv_color = (h, s, v)
        colors.append(color.ColorArray(color=hsv_color, color_space='hsv'))

        h += interval

    return colors


def generate_colormap_gradient_2_colors(color1, color2):
    colormap = color.Colormap([color1, color2])
    return colormap



