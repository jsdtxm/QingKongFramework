# Application Configuration

> **Relevant source files**
> * [fastapp/apps/config.py](/fastapp/apps/config.py)
> * [fastapp/conf.py](/fastapp/conf.py)
> * [fastapp/exception_handlers.py](/fastapp/exception_handlers.py)
> * [fastapp/fastapi.py](/fastapp/fastapi.py)
> * [fastapp/misc/ascii_art.py](/fastapp/misc/ascii_art.py)

## Purpose and Scope

This document covers the configuration management system in QingKongFramework, which provides a centralized settings mechanism built on Pydantic Settings. The system handles environment variable loading, lazy initialization, and provides type-safe configuration access throughout the framework.

For information about application discovery and the `INSTALLED_APPS` setting, see [Application Discovery and Structure](Application-Discovery-and-Structure.md). For database-specific configuration, see [Database Management](Database-Management.md).

## Configuration Architecture

The configuration system consists of two main classes that work together to provide flexible, type-safe settings management:

```mermaid
flowchart TD

BaseSettings["BaseSettings<br>(PydanticBaseSettings)"]
LazySettings["LazySettings<br>(Proxy/Wrapper)"]
ProjectSettings["common.settings.Settings<br>(User Implementation)"]
EnvVars["Environment Variables<br>(QK_ prefix)"]
DefaultValues["Default Values<br>(in BaseSettings)"]
FastAPI["FastAPI Application"]
AppConfig["AppConfig System"]
Middleware["Middleware Stack"]
RateLimiter["Rate Limiter"]
PydanticBaseSettings["PydanticBaseSettings"]
settings["settings instance<br>(Global)"]

PydanticBaseSettings --> BaseSettings
LazySettings --> settings
EnvVars --> BaseSettings
DefaultValues --> BaseSettings
settings --> FastAPI
settings --> AppConfig
settings --> Middleware
settings --> RateLimiter

subgraph subGraph2 ["Framework Components"]
    FastAPI
    AppConfig
    Middleware
    RateLimiter
end

subgraph Environment ["Environment"]
    EnvVars
    DefaultValues
end

subgraph subGraph0 ["Configuration Classes"]
    BaseSettings
    LazySettings
    ProjectSettings
    BaseSettings --> ProjectSettings
    ProjectSettings --> LazySettings
end
```

**Sources:** [fastapp/conf.py L11-L133](/fastapp/conf.py#L11-L133)

 [fastapp/fastapi.py L19](/fastapp/fastapi.py#L19-L19)

 [fastapp/apps/config.py L46](/fastapp/apps/config.py#L46-L46)

## Core Configuration Classes

### BaseSettings Class

The `BaseSettings` class extends Pydantic's `BaseSettings` to provide the foundation for all configuration in the framework:

```mermaid
classDiagram
    class BaseSettings {
        +model_config: SettingsConfigDict
        +PROJECT_NAME: Optional[str]
        +TIME_ZONE: str
        +BASE_DIR: Path
        +SECRET_KEY: str
        +ALLOWED_HOSTS: List[str]
        +INSTALLED_APPS: List[str]
        +MIDDLEWARE: List[str]
        +DATABASES: dict
        +CACHES: dict
        +AUTH_USER_MODEL: str
        +ACCESS_TOKEN_LIFETIME: int
        +EMAIL_BACKEND: str
        +DEFAULT_PAGINATION_CLASS: Optional[str]
    }
    class PydanticBaseSettings {
        «external»
    }
    class LazySettings {
        +settings: Optional[BaseSettings]
        +load_settings() : BaseSettings
        +getattr(name: str) : Any
    }
    PydanticBaseSettings <|-- BaseSettings : loads
    LazySettings <-- BaseSettings
```

**Sources:** [fastapp/conf.py L11-L94](/fastapp/conf.py#L11-L94)

### LazySettings Implementation

The `LazySettings` class provides lazy initialization of settings, loading them only when first accessed:

| Method | Purpose | Implementation |
| --- | --- | --- |
| `load_settings()` | Loads settings from `common.settings` | Imports and caches settings instance |
| `__getattr__()` | Proxy attribute access | Delegates to loaded settings instance |
| `__init__()` | Initialize with no settings | Sets `self.settings = None` |

**Sources:** [fastapp/conf.py L95-L132](/fastapp/conf.py#L95-L132)

## Configuration Categories

The framework organizes configuration into logical categories:

### Core Framework Settings

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `PROJECT_NAME` | `Optional[str]` | `None` | Project identifier |
| `BASE_DIR` | `Path` | Required | Project root directory |
| `SECRET_KEY` | `str` | `"longlivethegreatunityofthepeople"` | Cryptographic secret |
| `TIME_ZONE` | `str` | `"Asia/Shanghai"` | Default timezone |
| `ALLOWED_HOSTS` | `List[str]` | `["127.0.0.1", "localhost"]` | Trusted host list |

### Application and Middleware Settings

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `INSTALLED_APPS` | `List[str]` | `[]` | Registered applications |
| `MIDDLEWARE` | `List[str]` | `["fastapp.middleware.trustedhost.TrustedHostMiddleware"]` | Middleware stack |
| `NO_EXPORT_APPS` | `List[str]` | `[]` | Apps excluded from port mapping |

### Database and Caching

| Setting | Type | Description |
| --- | --- | --- |
| `DATABASES` | `dict[str, dict[str, Any]]` | Database connection configurations |
| `CACHES` | `dict[str, dict[str, Any]]` | Cache backend configurations |

**Sources:** [fastapp/conf.py L14-L94](/fastapp/conf.py#L14-L94)

## Environment Variable Support

The configuration system automatically loads environment variables with the `QK_` prefix:

```mermaid
flowchart TD

QK_PROJECT_NAME["QK_PROJECT_NAME"]
QK_SECRET_KEY["QK_SECRET_KEY"]
QK_TIME_ZONE["QK_TIME_ZONE"]
QK_ALLOWED_HOSTS["QK_ALLOWED_HOSTS"]
PROJECT_NAME["PROJECT_NAME"]
SECRET_KEY["SECRET_KEY"]
TIME_ZONE["TIME_ZONE"]
ALLOWED_HOSTS["ALLOWED_HOSTS"]

QK_PROJECT_NAME --> PROJECT_NAME
QK_SECRET_KEY --> SECRET_KEY
QK_TIME_ZONE --> TIME_ZONE
QK_ALLOWED_HOSTS --> ALLOWED_HOSTS

subgraph subGraph1 ["BaseSettings Fields"]
    PROJECT_NAME
    SECRET_KEY
    TIME_ZONE
    ALLOWED_HOSTS
end

subgraph subGraph0 ["Environment Variables"]
    QK_PROJECT_NAME
    QK_SECRET_KEY
    QK_TIME_ZONE
    QK_ALLOWED_HOSTS
end
```

**Sources:** [fastapp/conf.py L12](/fastapp/conf.py#L12-L12)

## Settings Loading and Usage Flow

The framework uses a lazy loading pattern to ensure settings are available throughout the application lifecycle:

```mermaid
sequenceDiagram
  participant Application Startup
  participant LazySettings Instance
  participant common.settings
  participant BaseSettings Class
  participant Framework Component

  Application Startup->>LazySettings Instance: Import settings
  note over LazySettings Instance: settings = LazySettings()
  Framework Component->>LazySettings Instance: Access settings.MIDDLEWARE
  LazySettings Instance->>LazySettings Instance: load_settings()
  loop [Settings not loaded]
    LazySettings Instance->>common.settings: Import project settings
    common.settings->>BaseSettings Class: Instantiate with env vars
    BaseSettings Class-->>common.settings: Configured instance
    common.settings-->>LazySettings Instance: Return settings
    LazySettings Instance->>LazySettings Instance: Cache settings
  end
  LazySettings Instance->>Framework Component: Return MIDDLEWARE value
```

**Sources:** [fastapp/conf.py L109-L129](/fastapp/conf.py#L109-L129)

 [fastapp/fastapi.py L91-L97](/fastapp/fastapi.py#L91-L97)

## Integration with Framework Components

### FastAPI Application Setup

The configuration system integrates tightly with the FastAPI application initialization:

```mermaid
flowchart TD

LoadApps["init_apps(settings.INSTALLED_APPS)"]
LoadModels["init_models()"]
LoadDB["async_init_db(get_tortoise_config(settings.DATABASES))"]
LoadMiddleware["Load settings.MIDDLEWARE"]
LoadHealthz["Check settings.INCLUDE_HEALTHZ"]
INSTALLED_APPS["settings.INSTALLED_APPS"]
DATABASES["settings.DATABASES"]
MIDDLEWARE["settings.MIDDLEWARE"]
INCLUDE_HEALTHZ["settings.INCLUDE_HEALTHZ"]
ALLOWED_HOSTS["settings.ALLOWED_HOSTS"]

INSTALLED_APPS --> LoadApps
DATABASES --> LoadDB
MIDDLEWARE --> LoadMiddleware
INCLUDE_HEALTHZ --> LoadHealthz
ALLOWED_HOSTS --> LoadMiddleware

subgraph subGraph1 ["Settings Usage"]
    INSTALLED_APPS
    DATABASES
    MIDDLEWARE
    INCLUDE_HEALTHZ
    ALLOWED_HOSTS
end

subgraph FastAPI.__init__ ["FastAPI.init"]
    LoadApps
    LoadModels
    LoadDB
    LoadMiddleware
    LoadHealthz
end
```

**Sources:** [fastapp/fastapi.py L79-L109](/fastapp/fastapi.py#L79-L109)

### AppConfig Integration

The `AppConfig` class also relies on settings for port management and application configuration:

| Setting Used | Purpose in AppConfig |
| --- | --- |
| `settings.ENABLE_PORT_MAP_FILE` | Controls port file generation |
| `settings.PROJECT_NAME` | Used in port lock file naming |
| `settings.BASE_DIR.name` | Fallback for lock file naming |
| `settings.NO_EXPORT_APPS` | Excludes apps from port assignment |

**Sources:** [fastapp/apps/config.py L46-L64](/fastapp/apps/config.py#L46-L64)

## Configuration Extension Pattern

Users extend the configuration system by creating their own settings class in `common.settings`:

```mermaid
flowchart TD

UserSettings["common/settings.py<br>Settings(BaseSettings)"]
UserValues["Custom configuration values"]
BaseSettings["fastapp.conf.BaseSettings"]
LazySettings["fastapp.conf.LazySettings"]
GlobalSettings["fastapp.conf.settings"]

BaseSettings --> UserSettings
UserSettings --> LazySettings

subgraph Framework ["Framework"]
    BaseSettings
    LazySettings
    GlobalSettings
    LazySettings --> GlobalSettings
end

subgraph subGraph0 ["User Project"]
    UserSettings
    UserValues
    UserValues --> UserSettings
end
```

**Sources:** [fastapp/conf.py L120-L125](/fastapp/conf.py#L120-L125)