# Custom warning function with blue text
def custom_warn(message, category=UserWarning):
    # ANSI escape codes for white text on red background
    red_background = "\033[41m"
    white_text = "\033[97m"
    reset_color = "\033[0m"
    print(f"{red_background}{white_text} {message} {reset_color}")