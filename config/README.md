# config/

All runtime configuration flows through **environment variables** with the `SCI_`
prefix (see `backend/app/core/config.py` and the root `.env.example`).

Nothing sensitive belongs in this folder. If static config files become necessary
(e.g. rule overrides), add them here as JSON and document them in this README.
