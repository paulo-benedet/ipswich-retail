# Issue 13 Browse products

Login now opens /products/. The authenticated catalogue reads product names, GBP prices, descriptions, categories and availability from the database. The layout follows the approved product prototype. Search, category and basket controls are visible but disabled pending their stories. The basket summary is a zero-value placeholder, not a working basket.

The migration creates the product table without changing customer accounts. The seed_products command inserts six missing sample products by unique SKU, including an out-of-stock example. Re-running preserves existing data. Docker Compose and hosted startup run migration and seeding automatically.

## Windows installation

Select branch 13-browse-products and copy the archive contents into the repository root (the folder containing manage.py), preserving folder paths and replacing matching files. No database or credentials are included.

For local Python, run each command separately in PowerShell:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
```

```powershell
.\.venv\Scripts\python.exe manage.py seed_products
```

```powershell
.\.venv\Scripts\python.exe manage.py test
```

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Alternatively rebuild Docker with `docker compose up --build -d`.

Open http://127.0.0.1:8000/ and sign in with a local account. Confirm six products, prices, availability and an out-of-stock woven throw. Check the narrow-screen layout. The hosted database and local database have separate accounts.

Commit and push the changes to the feature branch. CI runs existing and catalogue tests, including browser tests. After the pull request is merged, check the deployed catalogue before marking issue 13 Done. Search, filters and basket functionality are deferred to their respective issues.

## Prototype correction

Migration 0002 updates only the original six sample records whose fields still exactly match the first package; edited or custom records are preserved. Fresh databases receive the prototype products from seed_products. The prototype illustrative basket selection is not preloaded. Product artwork is served as local SVG files.
