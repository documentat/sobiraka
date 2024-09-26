from colorama import Back, Fore

from sobiraka.models import PageStatus

ICONS = {
    PageStatus.INITIALIZE: f'{Fore.LIGHTMAGENTA_EX}┄',
    PageStatus.PREPARE: f'{Fore.LIGHTMAGENTA_EX}┄',
    PageStatus.PROCESS1: f'{Fore.LIGHTGREEN_EX}─',
    PageStatus.PROCESS2: f'{Fore.LIGHTGREEN_EX}━',
    PageStatus.PROCESS3: f'{Fore.LIGHTCYAN_EX}━',
    PageStatus.PROCESS4: f'{Fore.GREEN}━',

    PageStatus.FAILURE: f'{Back.LIGHTRED_EX}{Fore.WHITE}X',
    PageStatus.DEP_FAILURE: f'{Back.LIGHTYELLOW_EX}{Fore.BLACK}!',
    PageStatus.VOL_FAILURE: f'{Fore.LIGHTGREEN_EX}━',  # identical to PROCESS2
}
COLORS = {
    PageStatus.FAILURE: Fore.RED,
    PageStatus.DEP_FAILURE: Fore.LIGHTYELLOW_EX,
}
