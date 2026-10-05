"""update user model for coursecraft

Revision ID: 646d7a3afc55
Revises: e2cab78712ec
Create Date: 2026-09-30 22:48:31.449240

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '646d7a3afc55'
down_revision: Union[str, Sequence[str], None] = 'e2cab78712ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop old students table (Student Management leftover)
    op.drop_index(op.f('ix_students_email'), table_name='students')
    op.drop_index(op.f('ix_students_id'), table_name='students')
    op.drop_index(op.f('ix_students_name'), table_name='students')
    op.drop_table('students')

    # Remove any old user data (old schema is incompatible)
    op.execute("DELETE FROM users")

    # Add new columns
    op.add_column('users', sa.Column('name', sa.String(), nullable=False))
    op.add_column('users', sa.Column('email', sa.String(), nullable=False))
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=False))
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='student'))

    # Update indexes
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_name'), 'users', ['name'], unique=False)

    # Drop old columns
    op.drop_column('users', 'username')
    op.drop_column('users', 'hashed_password')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('users', sa.Column('hashed_password', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('username', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_index(op.f('ix_users_name'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.drop_column('users', 'role')
    op.drop_column('users', 'password_hash')
    op.drop_column('users', 'email')
    op.drop_column('users', 'name')
    op.create_table('students',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('grade', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('students_pkey'))
    )
    op.create_index(op.f('ix_students_name'), 'students', ['name'], unique=False)
    op.create_index(op.f('ix_students_id'), 'students', ['id'], unique=False)
    op.create_index(op.f('ix_students_email'), 'students', ['email'], unique=True)
