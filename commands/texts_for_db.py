from aiogram.utils.formatting import Bold, as_list, as_marked_section


categories = ['Ремонт кузова', 'Покраска', 'Технический осмотр']

description_for_info_pages = {
    "main": "Добро пожаловать!",
    "about": "Петровская 71.\nРежим работы - c 9:00 до 17:00.",
    "payment": as_marked_section(
        Bold("Варианты оплаты:"),
        "Картой в боте",
        "Перевод",
        "Наличными",
        marker="✅ ",
    ).as_html(),
    "shipping": as_list(
        as_marked_section(
            Bold("Варианты доставки/заказа:"),
           "Только если сами зайдете",
            marker="✅ ",
        ),
        as_marked_section(Bold("Нельзя:"), "Почта", "Голуби", marker="❌ "),
        sep="\n----------------------\n",
    ).as_html(),
    'catalog': 'Категории:',
    'order': 'В корзине ничего нет!'
}



