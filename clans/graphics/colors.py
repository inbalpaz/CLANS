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
        #print(colors[i].hsv)
        #print(colors[i].rgb)

        h += interval

    return colors


def try_generate_colors():

    colors = []

    colors.append(color.ColorArray(color='red'))
    colors.append(color.ColorArray(color='blue'))
    colors.append(color.ColorArray(color='green'))
    colors.append(color.ColorArray(color='purple'))

    print("red")
    print(colors[0].hsv)
    print(colors[0].rgb)

    print("blue")
    print(colors[1].hsv)
    print(colors[1].rgb)

    print("green")
    print(colors[2].hsv)
    print(colors[2].rgb)

    print("purple")
    print(colors[3].hsv)
    print(colors[3].rgb)


