OAuth2 PKCE Flow
================

Aplikasi Android menggunakan library `AppAuth <https://github.com/openid/AppAuth-Android>`_
dengan PKCE (RFC 7636). Hanya metode ``S256`` yang didukung.

Konfigurasi Android App
-----------------------

.. list-table::
   :header-rows: 1

   * - Parameter
     - Nilai
   * - Authorization endpoint
     - ``{serverUrl}/oauth/authorize``
   * - Token endpoint
     - ``{serverUrl}/oauth/token``
   * - Redirect URI
     - ``com.example.timestudy://callback``
   * - Code challenge method
     - ``S256``

Alur Otorisasi
--------------

.. code-block:: text

   Android App                          Authorization Server
        |                                        |
        |-- GET /oauth/authorize?               |
        |   client_id=...                        |
        |   code_challenge=<S256(verifier)>     |
        |   redirect_uri=com.example...://callback  |
        |                                        |
        |          [HTML login form]             |
        |<-------------------------------------- |
        |                                        |
        |-- POST /oauth/authorize               |
        |   resp_id=R-001&pin=1234              |
        |                                        |
        |   302 -> redirect_uri?code=<code>      |
        |<-------------------------------------- |
        |                                        |
        |-- POST /oauth/token                   |
        |   code=<code>                          |
        |   code_verifier=<verifier>            |
        |                                        |
        |   { access_token, refresh_token }      |
        |<-------------------------------------- |

Daftar Client Baru
------------------

.. code-block:: bash

   curl -X POST http://localhost:8000/api/v1/oauth/clients \
     -H "Authorization: Bearer <admin_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "client_name": "TimeStudy Android",
       "redirect_uris": "com.example.timestudy://callback",
       "scope": "sync"
     }'

Server akan mengembalikan ``client_id`` yang perlu dikonfigurasi di Android app.
