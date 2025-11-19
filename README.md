<p align="left">
    <a href="README_CN.md">中文</a>&nbsp ｜ &nbspEnglish
</p>

# QingKongFramework (fastapp)

⚠️ **IMPORTANT: This repository contains documentation intended solely for AI consumption and does not provide documentation meant for human readers.**

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/jsdtxm/QingKongFramework)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview

QingKongFramework (package name: `fastapp`) is a full-stack async web framework built on top of FastAPI, designed to provide a Django-like development experience with full async support.

## Key Features

### 🚀 Django-Style Async Framework
- **No decorator overhead**: No need for `sync_to_async`, `aget`, or `afilter` - everything is natively async
- **Familiar patterns**: ModelViewSet, Serializers, FilterSets following Django REST Framework conventions

### 🗄️ Database Management
- **Multi-database support**: PostgreSQL, MySQL, SQLite via Tortoise ORM
- **Auto-migration system**: Automatic schema diff detection and migration generation
- **Fixture loading**: JSON-based data fixtures with FK/M2M relationship handling

### 🔐 Authentication & Authorization
- **JWT-based auth**: Built-in token authentication with configurable lifetimes
- **Permission system**: Model-based permission backend
- **Mixins**: LoginRequired, SuperUserRequired, Creator tracking

### ⚡ Performance & Scalability
- **Microservice mode**: Gateway + service architecture
- **Caching**: Redis-based caching with fastapi-cache2
- **Rate limiting**: Built-in rate limiter support

### 🛠️ Developer Tools
- **CLI commands**: `startapp`, `migrate`, `auto_migrate`, `loaddata`, `runserver`
- **Type safety**: Full Python 3.12+ type hints with mypy support
- **Nuitka compilation**: Optional binary compilation support

## Technology Stack

- **FastAPI** 0.115.4 - Modern async web framework
- **Tortoise ORM** 0.21.7 - Async ORM
- **Pydantic** 2.11.7 - Data validation
- **Uvicorn** 0.32.0 - ASGI server

## Requirements

- Python == 3.12

## Build

### nuitka
```
python -m build
```

### wheel
```
python setup-pure.py bdist_wheel
```

## Author

Vincent (jsdtxm@live.com)

## License

MIT License

