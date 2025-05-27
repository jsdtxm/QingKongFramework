from colorama import Back, Fore, Style, init
from colorama.ansi import code_to_chars

from fastapp.conf import settings

ascii_logo = r"""
    ______           __  ___    ____  ____ 
   / ____/___ ______/ /_/   |  / __ \/ __ \
  / /_  / __ `/ ___/ __/ /| | / /_/ / /_/ /
 / __/ / /_/ (__  ) /_/ ___ |/ ____/ ____/ 
/_/    \__,_/____/\__/_/  |_/_/   /_/      
                                           
"""


def print_logo(need_init=False):
    if need_init:
        init()

    logo = ascii_logo[1:-1]

    def apply_color_setting(logo, setting_value, color_module):
        if setting_value:
            if isinstance(setting_value, int):
                if color_module == Fore:
                    return code_to_chars(f"38;5;{setting_value}") + logo
                elif color_module == Back:
                    return code_to_chars(f"48;5;{setting_value}") + logo
            else:
                return getattr(color_module, setting_value) + logo
        return logo

    logo = apply_color_setting(logo, settings.LOGO_FORE, Fore)
    logo = apply_color_setting(logo, settings.LOGO_BACK, Back)
    logo = apply_color_setting(logo, settings.LOGO_STYLE, Style)

    print(logo)
    print(Style.RESET_ALL)
