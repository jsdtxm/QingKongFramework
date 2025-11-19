# Overview

> **Relevant source files**
> * [.trae/rules/project_rules.md](/.trae/rules/project_rules.md)
> * [.vscode/settings.json](/.vscode/settings.json)
> * [requirements.txt](/requirements.txt)

## Purpose and Scope

QingKongFramework is a comprehensive async web framework that provides a Django-like development experience built on top of FastAPI and Tortoise ORM. The framework enables developers to write fully asynchronous applications without the complexity typically associated with async Python development, eliminating the need for decorators like `sync_to_async` or async-specific ORM methods like `aget` or `afilter`.

This document provides a high-level overview of the entire framework architecture, its core innovations, and development patterns. For detailed information about specific subsystems, see:

* Core data operations: [FilterSet System](FilterSet-System.md) and [ModelSerializer System](ModelSerializer-System.md)
* API development patterns: [ViewSets and CRUD Operations](ViewSets-and-CRUD-Operations.md)
* Database management: [Database Migrations and Schema](Database-Migrations-and-Schema.md)
* Command-line tools: [Command Line Interface](Command-Line-Interface.md)

Sources: [.trae/rules/project_rules.md L1-L5](/.trae/rules/project_rules.md#L1-L5)

 [requirements.txt L1-L65](/requirements.txt#L1-L65)

## Framework Architecture

QingKongFramework follows a layered architecture that bridges Django's familiar patterns with FastAPI's performance and async capabilities. The framework is structured around four primary layers that work together to provide a complete web development platform.

### High-Level System Architecture

```mermaid
flowchart TD

FastApp["fastapp.FastAPIApplication<br>Custom FastAPI Extensions"]
AppConfig["AppConfig System<br>INSTALLED_APPS Discovery"]
URLs["URL Routing<br>Django-style URL patterns"]
ViewSets["ViewSet System<br>ModelViewSet, GenericViewSet"]
Auth["Authentication<br>JWT, User Management"]
Filters["FilterBackend<br>Query Parameter Processing"]
Permissions["Permission System<br>Role-based Access Control"]
FilterSet["FilterSet System<br>Dynamic Query Filtering"]
ModelSerializer["ModelSerializer<br>Tortoise-Pydantic Bridge"]
BaseModel["BaseModel Extensions<br>Enhanced Tortoise Models"]
DBUtils["Database Utilities<br>Migrations, Schema Generation"]
CLI["Management Commands<br>runserver, migrate, startapp"]
Cache["Multi-Backend Cache<br>Redis, Disk, PostgreSQL"]
Gateway["API Gateway<br>Load Balancing, Routing"]
FastAPICore["FastAPI<br>ASGI Web Framework"]
TortoiseORM["Tortoise ORM<br>Async Database Toolkit"]
Pydantic["Pydantic<br>Data Validation"]

AppConfig --> ViewSets
ViewSets --> FilterSet
ViewSets --> ModelSerializer
Filters --> FilterSet
BaseModel --> TortoiseORM
ModelSerializer --> Pydantic
CLI --> FastApp
CLI --> DBUtils
Cache --> ViewSets
Gateway --> FastApp
FastApp --> FastAPICore
ViewSets --> FastAPICore
Auth --> FastAPICore

subgraph subGraph4 ["External Dependencies"]
    FastAPICore
    TortoiseORM
    Pydantic
end

subgraph subGraph3 ["Infrastructure Layer"]
    CLI
    Cache
    Gateway
end

subgraph subGraph2 ["Data Layer"]
    FilterSet
    ModelSerializer
    BaseModel
    DBUtils
    FilterSet --> BaseModel
    ModelSerializer --> BaseModel
    DBUtils --> BaseModel
end

subgraph subGraph1 ["API Layer"]
    ViewSets
    Auth
    Filters
    Permissions
    ViewSets --> Auth
    ViewSets --> Permissions
end

subgraph subGraph0 ["Application Layer"]
    FastApp
    AppConfig
    URLs
    FastApp --> AppConfig
    FastApp --> URLs
end
```

Sources: [.trae/rules/project_rules.md L8-L41](/.trae/rules/project_rules.md#L8-L41)

 [requirements.txt L5-L24](/requirements.txt#L5-L24)

## Core Innovations

The framework's primary innovation lies in its dynamic model generation system that automatically creates Pydantic models from Tortoise ORM definitions. This system consists of two interconnected components that work through Python metaclasses to provide seamless integration between the ORM layer and API serialization.

### Dynamic Model Generation Flow

```mermaid
sequenceDiagram
  participant Django-style App
  participant Metaclass System
  participant FilterSet Instance
  participant ModelSerializer Instance
  participant Tortoise BaseModel
  participant Generated Pydantic Model
  participant ViewSet API

  Django-style App->>Metaclass System: "Define FilterSet/ModelSerializer classes"
  Metaclass System->>Tortoise BaseModel: "Introspect model fields and relationships"
  Metaclass System->>Generated Pydantic Model: "Generate dynamic Pydantic models"
  ViewSet API->>FilterSet Instance: "Process query parameters"
  FilterSet Instance->>Generated Pydantic Model: "Validate filter parameters"
  FilterSet Instance->>Tortoise BaseModel: "Build filtered QuerySet"
  Tortoise BaseModel->>ModelSerializer Instance: "Return query results"
  ModelSerializer Instance->>Generated Pydantic Model: "Serialize response data"
  ModelSerializer Instance->>ViewSet API: "Return validated JSON response"
```

The `FilterSet` system automatically generates Pydantic models for query parameter validation, while `ModelSerializer` creates models for request/response serialization. Both systems eliminate the need for manual Pydantic model definitions while maintaining full type safety and validation.

Sources: [.trae/rules/project_rules.md L116-L154](/.trae/rules/project_rules.md#L116-L154)

## Framework Structure

QingKongFramework organizes code using Django's familiar app-based structure, where each application contains models, views, serializers, filters, and URL configurations. This modular approach supports both monolithic and microservice architectures.

### Application Structure and Component Relationships

```mermaid
flowchart TD

ManagePy["manage.py<br>CLI Entry Point"]
Settings["settings.py<br>Configuration"]
MainURLs["urls.py<br>Root URL Configuration"]
Models["models.py<br>BaseModel Definitions"]
Views["views.py<br>ModelViewSet Classes"]
Serializers["serializers.py<br>ModelSerializer Classes"]
Filters["filters.py<br>FilterSet Classes"]
AppURLs["urls.py<br>App URL Patterns"]
Fixtures["fixtures/<br>JSON Data Files"]
FastAppCore["FastAPIApplication<br>Extended FastAPI"]
ViewSetSystem["viewsets/<br>ModelViewSet, GenericViewSet"]
FilterSystem["filters/<br>FilterSet, FilterBackend"]
SerializerSystem["serializers/<br>ModelSerializer"]
ModelSystem["models/<br>BaseModel Extensions"]
CLISystem["management/<br>Command Classes"]

ManagePy --> CLISystem
Settings --> FastAppCore
MainURLs --> AppURLs
Models --> ModelSystem
Views --> ViewSetSystem
Serializers --> SerializerSystem
Filters --> FilterSystem

subgraph subGraph2 ["Core Framework: fastapp/"]
    FastAppCore
    ViewSetSystem
    FilterSystem
    SerializerSystem
    ModelSystem
    CLISystem
    CLISystem --> FastAppCore
end

subgraph subGraph1 ["App Structure: apps/{app_name}/"]
    Models
    Views
    Serializers
    Filters
    AppURLs
    Fixtures
    Models --> Views
    Models --> Serializers
    Models --> Filters
    Views --> Serializers
    Views --> Filters
    AppURLs --> Views
    Fixtures --> Models
end

subgraph subGraph0 ["Project Root"]
    ManagePy
    Settings
    MainURLs
end
```

Each app follows the Model-View-Serializer-Filter pattern, where models define data structures, views handle HTTP requests, serializers manage data transformation, and filters provide query parameter processing.

Sources: [.trae/rules/project_rules.md L44-L54](/.trae/rules/project_rules.md#L44-L54)

 [.trae/rules/project_rules.md L76-L114](/.trae/rules/project_rules.md#L76-L114)

 [.trae/rules/project_rules.md L236-L247](/.trae/rules/project_rules.md#L236-L247)

## Key Technologies and Dependencies

The framework builds upon a carefully selected stack of modern Python libraries optimized for async performance and developer productivity. The dependency structure emphasizes async-first libraries and avoids synchronous bottlenecks.

| Category | Technology | Version | Purpose |
| --- | --- | --- | --- |
| Web Framework | `fastapi` | 0.115.4 | ASGI web framework and API routing |
| ORM | `tortoise-orm` | 0.21.7 | Async database toolkit and query builder |
| Validation | `pydantic` | 2.11.7 | Data validation and serialization |
| Server | `uvicorn` | 0.32.0 | ASGI server with uvloop acceleration |
| Database | `asyncmy`, `aiosqlite` | 0.2.9, 0.20.0 | Async MySQL and SQLite drivers |
| Caching | `redis`, `diskcache` | 4.6.0, 5.6.3 | Multi-backend caching system |
| Authentication | `pyjwt`, `bcrypt` | 2.10.1, 4.2.1 | JWT tokens and password hashing |
| CLI | `click`, `colorama` | 8.1.7, 0.4.6 | Command-line interface and colored output |
| JSON | `orjson` | 3.10.15 | High-performance JSON serialization |
| Pagination | `fastapi-pagination` | 0.12.31 | API pagination with multiple backends |

The framework avoids traditional Django dependencies like `django` and `djangorestframework`, instead providing equivalent functionality through FastAPI-native implementations.

Sources: [requirements.txt L5-L65](/requirements.txt#L5-L65)

## Development Workflow

QingKongFramework provides a comprehensive command-line interface that mirrors Django's `manage.py` system while adding FastAPI-specific functionality. The CLI supports both single-process development mode and production microservice deployment.

### CLI Commands Overview

```mermaid
flowchart TD

StubGen["stubgen<br>Generate type stubs"]
Shell["shell<br>Interactive Python shell"]
Test["test<br>Run test suite"]
StartApp["startapp<br>Create new application"]
RunServerAIO["runserver-aio<br>Single process mode"]
CreateSuperUser["createsuperuser<br>Admin user creation"]
Migrate["migrate<br>Apply database migrations"]
AutoMigrate["auto_migrate<br>Auto-detect schema changes"]
LoadData["loaddata<br>Load JSON fixtures"]
ReverseGeneration["reverse_generation<br>Schema introspection"]
RunServer["runserver<br>Multi-service mode"]
Gateway["gateway<br>API gateway server"]
ServeStatic["serve_static<br>Static file server"]

StartApp --> Migrate
LoadData --> RunServerAIO
AutoMigrate --> RunServer

subgraph subGraph2 ["Production Commands"]
    RunServer
    Gateway
    ServeStatic
    RunServer --> Gateway
end

subgraph subGraph1 ["Database Commands"]
    Migrate
    AutoMigrate
    LoadData
    ReverseGeneration
    Migrate --> LoadData
end

subgraph subGraph0 ["Development Commands"]
    StartApp
    RunServerAIO
    CreateSuperUser
end

subgraph subGraph3 ["Utility Commands"]
    StubGen
    Shell
    Test
end
```

The development workflow typically follows: create app → define models → run migrations → load fixtures → start development server. For production deployment, the framework supports containerized microservice architecture with API gateway routing.

Sources: [.trae/rules/project_rules.md L206-L216](/.trae/rules/project_rules.md#L206-L216)

 [.trae/rules/project_rules.md L155-L203](/.trae/rules/project_rules.md#L155-L203)

## Framework Philosophy

QingKongFramework bridges the gap between Django's developer-friendly patterns and FastAPI's async performance by providing:

* **Familiar Django Patterns**: Models, views, serializers, and URL routing that Django developers recognize
* **Async-First Design**: No need for `sync_to_async` decorators or async-specific ORM methods
* **Automatic Code Generation**: Dynamic Pydantic model creation eliminates boilerplate
* **Type Safety**: Full mypy compatibility with automatic type stub generation
* **Microservice Ready**: Built-in API gateway and service discovery support
* **Production Focused**: Docker containerization and multi-backend caching out of the box

This approach allows teams to leverage Django's proven architectural patterns while achieving FastAPI's performance characteristics in fully asynchronous applications.

Sources: [.trae/rules/project_rules.md L1-L6](/.trae/rules/project_rules.md#L1-L6)

 [.vscode/settings.json L1-L16](/.vscode/settings.json#L1-L16)