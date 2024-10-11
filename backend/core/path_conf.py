#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from pathlib import Path

# Get project root directory
# Or use an absolute path, pointing to the backend directory, for example on Windows: BasePath = D:\git_project\fastapi_mysql\backend
BasePath = Path(__file__).resolve().parent.parent

# Alembic migration file storage path
ALEMBIC_Versions_DIR = os.path.join(BasePath, 'alembic', 'versions')

# Log file path
LOG_DIR = os.path.join(BasePath, 'log')

# Offline IP database path
IP2REGION_XDB = os.path.join(BasePath, 'static', 'ip2region.xdb')

# Mount static directory
STATIC_DIR = os.path.join(BasePath, 'static')

# Jinja2 template file path
JINJA2_TEMPLATE_DIR = os.path.join(BasePath, 'templates')