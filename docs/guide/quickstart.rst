Quick Start
===========

Requirements
------------

- Python 3.11+
- ``pip install -e ".[dev]"`` untuk install semua dependency

Jalankan server
---------------

.. code-block:: bash

   uvicorn app.main:app --reload

API tersedia di ``http://localhost:8000``.

Migrasi database
----------------

.. code-block:: bash

   alembic upgrade head
   python scripts/seed.py   # buat admin awal dan OAuth2 client default

Endpoint utama
--------------

.. list-table::
   :header-rows: 1

   * - Endpoint
     - Keterangan
   * - ``GET /docs``
     - Swagger UI
   * - ``GET /redoc``
     - ReDoc
   * - ``POST /api/v1/auth/login``
     - Login admin
   * - ``GET /oauth/authorize``
     - OAuth2 authorization page
   * - ``POST /oauth/token``
     - Token exchange / refresh

Build dokumentasi lokal
-----------------------

.. code-block:: bash

   pip install -e ".[dev]"
   sphinx-build docs docs/_build/html
   # buka docs/_build/html/index.html
