from sqlalchemy import DateTime, String, Text, Float, func, Numeric, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import OrderStatuses

# 0 «Новая», 
# 1 «Согласование»,
# 2 «В работе»,
# 3 «Ожидание запчастей»,
# 4 «Контроль качества»,
# 5 «Готов к выдаче»,
# 6 «Выдан»
# 7 «Отменен»