<p align="left">
    中文&nbsp ｜ &nbsp<a href="README.md">English</a>
</p>

# QingKongFramework (fastapp)

⚠️ **重要提示：本仓库中的文档仅用于 AI 解析，不面向人类读者提供可读性文档。**

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/jsdtxm/QingKongFramework)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 概述

QingKongFramework（包名：`fastapp`）是一个基于 FastAPI 构建的全栈异步 Web 框架，旨在提供类似 Django 的开发体验，并全面支持异步操作。

## 核心特性

### 🚀 类 Django 风格的异步框架
- **无装饰器开销**：无需使用 `sync_to_async`、`aget` 或 `afilter` —— 所有功能原生支持异步
- **熟悉的设计模式**：遵循 Django REST Framework 规范的 ModelViewSet、序列化器（Serializers）和过滤器集（FilterSets）

### 🗄️ 数据库管理
- **多数据库支持**：通过 Tortoise ORM 支持 PostgreSQL、MySQL 和 SQLite
- **自动迁移系统**：自动检测数据库结构差异并生成迁移脚本
- **Fixture 数据加载**：支持基于 JSON 的数据填充，可处理外键（FK）和多对多（M2M）关系

### 🔐 认证与授权
- **基于 JWT 的认证**：内置 Token 认证机制，支持配置令牌有效期
- **权限系统**：基于模型的权限后端
- **Mixin 支持**：如 LoginRequired、SuperUserRequired、创建者追踪等

### ⚡ 性能与可扩展性
- **微服务模式**：支持网关 + 服务架构
- **缓存机制**：基于 Redis，集成 fastapi-cache2
- **限流功能**：内置请求频率限制支持

### 🛠️ 开发者工具
- **CLI 命令**：提供 `startapp`、`migrate`、`auto_migrate`、`loaddata`、`runserver` 等命令
- **类型安全**：完整支持 Python 3.12+ 类型注解，兼容 mypy
- **Nuitka 编译**：可选的二进制编译支持

## 技术栈

- **FastAPI** 0.115.4 - 现代异步 Web 框架  
- **Tortoise ORM** 0.21.7 - 异步 ORM  
- **Pydantic** 2.11.7 - 数据验证  
- **Uvicorn** 0.32.0 - ASGI 服务器  

## 要求

- Python == 3.12

## 构建方式

### 使用 nuitka
```bash
python -m build
```

### 构建 wheel 包
```bash
python setup-pure.py bdist_wheel
```

## 作者

Vincent (jsdtxm@live.com)

## 许可证

MIT