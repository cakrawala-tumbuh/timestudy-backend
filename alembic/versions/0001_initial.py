"""Initial schema — create all tables.

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False),
        sa.Column("email", sa.String(254), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_superuser", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "respondents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resp_id", sa.String(20), unique=True, nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(254), unique=True, nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("position", sa.String(100), nullable=True),
        sa.Column("pin_hash", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_respondents_resp_id", "respondents", ["resp_id"])

    op.create_table(
        "daily_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resp_id", sa.String(20), sa.ForeignKey("respondents.resp_id", ondelete="CASCADE"), nullable=False),
        sa.Column("tanggal", sa.String(10), nullable=False),
        sa.Column("jam_masuk", sa.String(5), nullable=False),
        sa.Column("jam_pulang", sa.String(5), nullable=False),
        sa.Column("menit_istirahat", sa.Integer(), default=60),
        sa.Column("total_jam_hitung", sa.Float(), nullable=True),
        sa.Column("day_color", sa.String(1), default="G"),
        sa.Column("pct_core", sa.Float(), default=0.0),
        sa.Column("pct_copilot", sa.Float(), default=0.0),
        sa.Column("pct_character", sa.Float(), default=0.0),
        sa.Column("pct_improve", sa.Float(), default=0.0),
        sa.Column("pct_strategic", sa.Float(), default=0.0),
        sa.Column("pct_admin", sa.Float(), default=0.0),
        sa.Column("pct_recovery", sa.Float(), default=0.0),
        sa.Column("total_pct", sa.Float(), default=0.0),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_synced", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("resp_id", "tanggal", name="uq_daily_log_resp_date"),
    )
    op.create_index("ix_daily_logs_resp_id", "daily_logs", ["resp_id"])

    op.create_table(
        "oauth_clients",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("client_id", sa.String(48), unique=True, nullable=False),
        sa.Column("client_name", sa.String(100), nullable=False),
        sa.Column("client_secret", sa.String(120), nullable=True),
        sa.Column("redirect_uris", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False, default="sync"),
        sa.Column("grant_types", sa.Text(), nullable=False),
        sa.Column("response_types", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_oauth_clients_client_id", "oauth_clients", ["client_id"])

    op.create_table(
        "oauth_authorization_codes",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("client_id", sa.String(48), nullable=False),
        sa.Column("resp_id", sa.String(20), nullable=False),
        sa.Column("code", sa.String(128), unique=True, nullable=False),
        sa.Column("code_challenge", sa.String(128), nullable=False),
        sa.Column("code_challenge_method", sa.String(10), nullable=False, default="S256"),
        sa.Column("redirect_uri", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False, default="sync"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_oauth_authorization_codes_code", "oauth_authorization_codes", ["code"])

    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("client_id", sa.String(48), nullable=False),
        sa.Column("resp_id", sa.String(20), nullable=False),
        sa.Column("access_token", sa.String(512), unique=True, nullable=False),
        sa.Column("refresh_token", sa.String(512), unique=True, nullable=True),
        sa.Column("token_type", sa.String(20), nullable=False, default="Bearer"),
        sa.Column("scope", sa.Text(), nullable=False, default="sync"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_oauth_tokens_access_token", "oauth_tokens", ["access_token"])
    op.create_index("ix_oauth_tokens_resp_id", "oauth_tokens", ["resp_id"])


def downgrade() -> None:
    op.drop_table("oauth_tokens")
    op.drop_table("oauth_authorization_codes")
    op.drop_table("oauth_clients")
    op.drop_table("daily_logs")
    op.drop_table("respondents")
    op.drop_table("users")
