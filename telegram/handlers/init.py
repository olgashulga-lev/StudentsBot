from aiogram import Dispatcher

from . import common
from . import registration
from . import player
from . import shop
from . import items

def registration_handlers(dp: Dispatcher):
    dp.iclude_routers(
        common.router,
        registration.router,
        player.router,
        shop.router,
        items.router,
    )
