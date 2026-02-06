from aiogram import types
from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.Paginator import Paginator
from database.Banner import orm_get_banner
from database.Category import orm_get_categories_inner_join_services
from database.Service import orm_get_services_by_category_id
from kbds.inline.main_menu_client import get_client_main_btns
from kbds.inline.inline import get_products_btns, get_user_catalog_btns


async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    kbds = get_client_main_btns(level=level)

    if not banner.image:
        return banner, kbds

    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    return image, kbds


async def catalog_menu(session, level, menu_name):
    banner = await orm_get_banner(session=session, page=menu_name)
    categories = await orm_get_categories_inner_join_services(session=session)
    print(categories)
    kbds = get_user_catalog_btns(level=level, categories=categories)

    if not banner.image:
        return banner, kbds

    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    return image, kbds


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns[" Пред."] = "prev"
    if paginator.has_next():
        btns["След. "] = 'next'

    return btns


async def products_menu(session, level, category, page):
    products = await orm_get_services_by_category_id(session=session, category_id=category)
    paginator = Paginator(products, page)
    product = paginator.get_page()[0]
    image = InputMediaPhoto(
        media=product.image,
        caption=f"{product.name}\n \
            {product.description}\n Стоимость: {round(product.price, 2)}\n \
            Товар {paginator.page} из {paginator.pages}"
    )

    pagination_btns = pages(paginator)

    kbds = get_products_btns(
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
        product_id=product.id,
    )

    return image, kbds



async def order_menu(session, level, menu_name):
    ...


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        category: int | None = None,
        page: int | None = None,
):

    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog_menu(session, level, menu_name)
    elif level == 2:
        return await products_menu(session, level, category, page)
