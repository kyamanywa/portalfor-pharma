# PDF Downloads in Production — WeasyPrint + GTK3 Setup Guide

## Why PDFs work locally but NOT in production

WeasyPrint (the library that generates BMR PDFs) is a **Python package**, but it
depends on **GTK3 / Pango / Cairo** — which are **operating-system libraries**, not
Python packages.

| Environment | GTK3 present? | PDF works? |
|-------------|---------------|------------|
| Windows (local dev) | ✅ Bundled inside the WeasyPrint Windows wheel | ✅ Yes |
| Linux production server | ❌ Must be installed separately via `apt`/`yum` | ❌ No |

`pip install weasyprint` alone is **not enough** on Linux.  
You must also install the system packages shown below.

---

## Step 1 — Install system libraries on the production server

SSH into your server and run the block that matches your OS:

### Ubuntu / Debian (most common)
```bash
sudo apt-get update
sudo apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libcairo-gobject2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    python3-dev \
    gcc
```

### CentOS / RHEL / Amazon Linux (yum)
```bash
sudo yum install -y \
    pango \
    cairo \
    cairo-gobject \
    gdk-pixbuf2 \
    libffi-devel \
    python3-devel \
    gcc
```

### Fedora / RHEL 8+ (dnf)
```bash
sudo dnf install -y \
    pango \
    cairo \
    cairo-gobject \
    gdk-pixbuf2 \
    libffi-devel \
    python3-devel \
    gcc
```

### Alpine Linux / Docker
```bash
apk add --no-cache \
    pango \
    cairo \
    gdk-pixbuf \
    libffi-dev \
    musl-dev \
    gcc \
    ttf-dejavu
```

---

## Step 2 — Install / reinstall Python packages

After the system libraries are in place, reinstall WeasyPrint inside your
virtual environment so it links against the newly installed libraries:

```bash
# Activate your virtual environment first
source venv/bin/activate          # Linux/Mac
# or: venv\Scripts\activate       # Windows

pip install --upgrade pip
pip install -r requirements.txt
# If WeasyPrint was already installed, force a reinstall:
pip install --force-reinstall weasyprint==60.1
```

---

## Step 3 — Verify the fix

Run the built-in diagnostic command:

```bash
python manage.py check_pdf
```

Expected output when everything is working:
```
── 4. WeasyPrint render test
   ✅  PDF rendered successfully (12,345 bytes)

── 6. Summary
   ✅  PDF generation is WORKING — WeasyPrint is fully operational.
   BMR PDF downloads should work correctly in production.
```

If it still fails, run with `--fix` to get the exact install command:
```bash
python manage.py check_pdf --fix
```

To write a real test PDF to disk:
```bash
python manage.py check_pdf --test-file
# Then: ls -lh /tmp/weasyprint_test.pdf
```

---

## Step 4 — Redeploy (if using deploy.sh)

The `deploy.sh` script has been updated to install system dependencies
automatically. Simply re-run it:

```bash
bash deploy.sh
```

It will:
1. Detect your OS (apt / yum / dnf / apk)
2. Install the GTK3/Pango/Cairo system packages
3. Install Python requirements
4. Run a WeasyPrint smoke-test and report the result

---

## Docker / Container deployments

If you are running inside Docker, add the system packages to your `Dockerfile`
**before** the `pip install` step:

```dockerfile
# ── System dependencies for WeasyPrint ──────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 \
        libpangoft2-1.0-0 \
        libpangocairo-1.0-0 \
        libcairo2 \
        libcairo-gobject2 \
        libgdk-pixbuf2.0-0 \
        libffi-dev \
        shared-mime-info \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ──────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

---

## Hosting-platform specific notes

### Heroku
Add the **heroku-buildpack-apt** buildpack and create an `Aptfile`:
```
# Aptfile
libpango-1.0-0
libpangocairo-1.0-0
libcairo2
libgdk-pixbuf2.0-0
libffi-dev
shared-mime-info
```
Then add the buildpack:
```bash
heroku buildpacks:add --index 1 heroku-community/apt
```

### Railway / Render / Fly.io
These platforms use Docker under the hood — use the Dockerfile approach above.

### cPanel / Shared Hosting
WeasyPrint **cannot** run on shared hosting because you cannot install system
libraries. Use a VPS (DigitalOcean, Linode, AWS EC2, etc.) instead.

---

## Fallback behaviour

Even if WeasyPrint fails, the system will **not crash**. The code in
`bmr/views.py` has a three-level fallback chain:

```
WeasyPrint  →  xhtml2pdf  →  basic ReportLab text PDF
```

So users will always get *some* PDF, but only WeasyPrint produces the
professional, fully-formatted output that matches the official BMR documents.

---

## Quick reference — packages by library name

| Shared library | Ubuntu/Debian package | RHEL/CentOS package |
|---|---|---|
| `libpango-1.0.so.0` | `libpango-1.0-0` | `pango` |
| `libpangocairo-1.0.so.0` | `libpangocairo-1.0-0` | `pango` |
| `libcairo.so.2` | `libcairo2` | `cairo` |
| `libgdk_pixbuf-2.0.so.0` | `libgdk-pixbuf2.0-0` | `gdk-pixbuf2` |
| `libgobject-2.0.so.0` | `libglib2.0-0` | `glib2` |
| `libffi.so.*` | `libffi-dev` | `libffi-devel` |

---

*Last updated: 2026-05-07*
