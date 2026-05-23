TimeStudy Backend
=================

Backend API untuk aplikasi **TimeStudy** — manajemen data studi waktu kerja
dengan OAuth2 PKCE untuk sinkronisasi dari perangkat Android.

.. toctree::
   :maxdepth: 1
   :caption: Panduan

   guide/quickstart
   guide/oauth2

.. toctree::
   :maxdepth: 4
   :caption: API Reference

   autoapi/index

Overview
--------

.. list-table::
   :widths: 30 70

   * - **Framework**
     - FastAPI 0.115 + SQLAlchemy 2.0 (SQLite)
   * - **Auth (admin)**
     - JWT HS256 — access token 60 menit, refresh token 30 hari
   * - **Auth (responden)**
     - OAuth2 PKCE (RFC 7636) — AppAuth Android
   * - **API Docs (runtime)**
     - ``/docs`` (Swagger UI) · ``/redoc`` (ReDoc)
