import pygame


def inset_rect(rect, padding):
    """
    Shrinks a rect by padding on all sides.
    """
    return pygame.Rect(
        rect.x + padding,
        rect.y + padding,
        rect.width - padding * 2,
        rect.height - padding * 2
    )


def split_vertical(rect, top_ratio=0.5, gap=12):
    """
    Splits a rect into top and bottom parts.
    """
    top_height = int((rect.height - gap) * top_ratio)

    top = pygame.Rect(
        rect.x,
        rect.y,
        rect.width,
        top_height
    )

    bottom = pygame.Rect(
        rect.x,
        top.bottom + gap,
        rect.width,
        rect.height - top_height - gap
    )

    return top, bottom


def split_horizontal(rect, left_ratio=0.5, gap=12):
    """
    Splits a rect into left and right parts.
    """
    left_width = int((rect.width - gap) * left_ratio)

    left = pygame.Rect(
        rect.x,
        rect.y,
        left_width,
        rect.height
    )

    right = pygame.Rect(
        left.right + gap,
        rect.y,
        rect.width - left_width - gap,
        rect.height
    )

    return left, right


def stack_vertical(rect, heights, gap=10):
    """
    Creates vertical rectangles inside a parent rect.

    heights can contain:
    - int: fixed height
    - "fill": takes remaining space
    """
    fixed_total = 0
    fill_count = 0

    for h in heights:
        if h == "fill":
            fill_count += 1
        else:
            fixed_total += h

    total_gap = gap * (len(heights) - 1)
    remaining = rect.height - fixed_total - total_gap
    fill_height = max(0, remaining // max(1, fill_count))

    result = []
    y = rect.y

    for h in heights:
        if h == "fill":
            h = fill_height

        child = pygame.Rect(
            rect.x,
            y,
            rect.width,
            h
        )

        result.append(child)
        y += h + gap

    return result


def fit_text_to_width(text, font, max_width):
    """
    Shortens text with ... if it is too wide.
    """
    text = str(text)

    if font.size(text)[0] <= max_width:
        return text

    ellipsis = "..."

    while text and font.size(text + ellipsis)[0] > max_width:
        text = text[:-1]

    return text + ellipsis


def draw_wrapped_text_clamped(
    surface,
    text,
    font,
    color,
    x,
    y,
    max_width,
    line_height,
    max_bottom
):
    """
    Draws wrapped text but stops before max_bottom.
    This prevents text from overlapping fixed bottom UI.
    """
    words = str(text).split(" ")
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        test_surface = font.render(test_line, True, color)

        if test_surface.get_width() <= max_width:
            current_line = test_line
        else:
            if current_line:
                if y + line_height > max_bottom:
                    return y

                line_surface = font.render(current_line, True, color)
                surface.blit(line_surface, (x, y))
                y += line_height

            current_line = word + " "

    if current_line and y + line_height <= max_bottom:
        line_surface = font.render(current_line, True, color)
        surface.blit(line_surface, (x, y))
        y += line_height

    return y