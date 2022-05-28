from datetime import datetime

import sqlalchemy as sa

from database import Base


class BaseModelORM(Base):
    __abstract__ = True

    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    created_at = sa.Column(
        sa.DateTime, default=datetime.utcnow, server_default=sa.func.now()
    )
    updated_at = sa.Column(
        sa.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=sa.func.now(),
    )
