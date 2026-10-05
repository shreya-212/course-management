"""upgrade user model to coursely v2 uuid

Revision ID: ec533c8245ef
Revises: 646d7a3afc55
Create Date: 2026-10-04

This migration upgrades the users table from the CourseCraft v1 schema to
the finalized Coursely v2 schema:

  - id: INTEGER → UUID (primary key)
  - name → full_name (column rename)
  - role: VARCHAR(20) → PostgreSQL ENUM 'userrole' (admin, creator, student)
  - NEW: avatar_url (TEXT, nullable)
  - NEW: is_active (BOOLEAN, default true)
  - NEW: created_at (TIMESTAMPTZ)
  - NEW: updated_at (TIMESTAMPTZ)

EXISTING DATA:
  The database contains only 2 development/test users with integer IDs.
  These cannot be preserved when converting INTEGER → UUID primary keys
  (the values are incompatible types).  The previous migration
  (646d7a3afc55) also deleted all data for the same reason.

  Approach: clear existing test rows, then alter the table schema in-place.
  This avoids dropping/recreating the table and losing the Alembic history.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


# revision identifiers, used by Alembic.
revision: str = 'ec533c8245ef'
down_revision: Union[str, Sequence[str], None] = '646d7a3afc55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade to Coursely v2 User schema."""

    # ------------------------------------------------------------------
    # 1. Clear existing development data (integer IDs → UUID is lossy)
    # ------------------------------------------------------------------
    op.execute("DELETE FROM users")

    # Drop the integer sequence that backed the old serial PK
    op.execute("ALTER TABLE users ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS users_id_seq")

    # ------------------------------------------------------------------
    # 2. Create the PostgreSQL ENUM type for roles
    # ------------------------------------------------------------------
    userrole_enum = sa.Enum('admin', 'creator', 'student', name='userrole')
    userrole_enum.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # 3. Convert id column: INTEGER → UUID
    # ------------------------------------------------------------------
    # Change the column type using a USING clause (table is empty so cast is safe)
    op.execute(
        "ALTER TABLE users ALTER COLUMN id TYPE UUID "
        "USING gen_random_uuid()"
    )
    # Set UUID default for new rows
    op.execute(
        "ALTER TABLE users ALTER COLUMN id SET DEFAULT gen_random_uuid()"
    )

    # ------------------------------------------------------------------
    # 4. Rename name → full_name
    # ------------------------------------------------------------------
    op.alter_column('users', 'name', new_column_name='full_name')

    # Update the index (drop old, create new)
    op.drop_index('ix_users_name', table_name='users')
    op.create_index('ix_users_full_name', 'users', ['full_name'], unique=False)

    # ------------------------------------------------------------------
    # 5. Convert role column to use the ENUM type
    #    Must drop the VARCHAR default before changing type, then re-set it.
    # ------------------------------------------------------------------
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE userrole "
        "USING role::userrole"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN role SET DEFAULT 'student'"
    )

    # ------------------------------------------------------------------
    # 6. Add new columns
    # ------------------------------------------------------------------
    op.add_column('users', sa.Column(
        'avatar_url', sa.Text(), nullable=True,
    ))

    op.add_column('users', sa.Column(
        'is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'),
    ))

    op.add_column('users', sa.Column(
        'created_at',
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('now()'),
    ))

    op.add_column('users', sa.Column(
        'updated_at',
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('now()'),
    ))


def downgrade() -> None:
    """Revert to CourseCraft v1 User schema."""

    # Clear data (UUIDs can't convert back to serial integers meaningfully)
    op.execute("DELETE FROM users")

    # Drop new columns
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'avatar_url')

    # Revert role to VARCHAR(20)
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20) "
        "USING role::text"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN role SET DEFAULT 'student'::character varying"
    )

    # Revert id to serial INTEGER
    op.execute("ALTER TABLE users ALTER COLUMN id DROP DEFAULT")
    op.execute("ALTER TABLE users ALTER COLUMN id TYPE INTEGER USING 0")
    op.execute("CREATE SEQUENCE users_id_seq OWNED BY users.id")
    op.execute("ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass)")

    # Rename full_name → name
    op.drop_index('ix_users_full_name', table_name='users')
    op.alter_column('users', 'full_name', new_column_name='name')
    op.create_index('ix_users_name', 'users', ['name'], unique=False)

    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS userrole")
