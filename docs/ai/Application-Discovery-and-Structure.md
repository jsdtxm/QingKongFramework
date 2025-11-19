# Application Discovery and Structure

> **Relevant source files**
> * [fastapp/apps/config.py](/fastapp/apps/config.py)
> * [fastapp/conf.py](/fastapp/conf.py)
> * [fastapp/exception_handlers.py](/fastapp/exception_handlers.py)
> * [fastapp/fastapi.py](/fastapp/fastapi.py)
> * [fastapp/misc/ascii_art.py](/fastapp/misc/ascii_art.py)

This document covers the application discovery and loading system in QingKongFramework, including the `AppConfig` system, `INSTALLED_APPS` configuration, and modular application structure. This system provides Django-like application organization while integrating with FastAPI's routing and lifecycle management.

For configuration management details, see [Application Configuration](Application-Configuration.md). For ViewSet routing patterns, see [ViewSets and CRUD Operations](ViewSets-and-CRUD-Operations.md).

## Application Discovery Overview

The framework uses a sophisticated application discovery system that automatically detects, configures, and loads modular applications based on the `INSTALLED_APPS` setting. Each application is represented by an `AppConfig` instance that manages module loading, port assignment, and URL routing.

```mermaid
flowchart TD

INSTALLED_APPS["INSTALLED_APPS<br>List[str]"]
BaseSettings["BaseSettings<br>fastapp/conf.py"]
init_apps["init_apps()<br>fastapp/initialize/apps.py"]
AppConfigCreate["AppConfig.create()<br>fastapp/apps/config.py"]
AppConfigMeta["AppConfigMeta<br>Metaclass Magic"]
AppConfig["AppConfig<br>name, label, prefix, port"]
ModuleLoading["import_module()<br>Dynamic Module Loading"]
PortAssignment["Port Assignment<br>Automatic or Manual"]
URLLoading["load_url_module()<br>fastapp/fastapi.py"]
RouterInclude["FastAPI.include_router()"]
InternalViews["Internal Views<br>_cross_service endpoints"]

INSTALLED_APPS --> init_apps
AppConfigMeta --> AppConfig
AppConfig --> URLLoading
AppConfig --> InternalViews

subgraph subGraph3 ["Runtime Integration"]
    URLLoading
    RouterInclude
    InternalViews
    URLLoading --> RouterInclude
end

subgraph subGraph2 ["App Instance Management"]
    AppConfig
    ModuleLoading
    PortAssignment
    AppConfig --> ModuleLoading
    AppConfig --> PortAssignment
end

subgraph subGraph1 ["Discovery Engine"]
    init_apps
    AppConfigCreate
    AppConfigMeta
    init_apps --> AppConfigCreate
    AppConfigCreate --> AppConfigMeta
end

subgraph subGraph0 ["Configuration Layer"]
    INSTALLED_APPS
    BaseSettings
    BaseSettings --> INSTALLED_APPS
end
```

**Sources:** [fastapp/conf.py L27](/fastapp/conf.py#L27-L27)

 [fastapp/apps/config.py L31-L175](/fastapp/apps/config.py#L31-L175)

 [fastapp/fastapi.py L79-L126](/fastapp/fastapi.py#L79-L126)

## AppConfig System Architecture

The `AppConfig` class serves as the central configuration object for each application, with automatic attribute generation through its metaclass and flexible module discovery patterns.

### AppConfigMeta Metaclass

The `AppConfigMeta` metaclass automatically generates application metadata:

```mermaid
flowchart TD

ModulePath["module<br>'apps.user.apps'"]
AutoName["name = 'apps.user'<br>Extracted from module"]
AutoLabel["label = 'user'<br>Last component"]
AutoPrefix["prefix = 'user'<br>Database safe"]
Name["name: str<br>Full module path"]
Label["label: str<br>Short identifier"]
Prefix["prefix: str<br>Database prefix"]
Port["port: Optional[int]<br>Service port"]

AutoName --> Name
AutoLabel --> Label
AutoPrefix --> Prefix

subgraph subGraph1 ["AppConfig Attributes"]
    Name
    Label
    Prefix
    Port
end

subgraph subGraph0 ["Metaclass Processing"]
    ModulePath
    AutoName
    AutoLabel
    AutoPrefix
    ModulePath --> AutoName
    AutoName --> AutoLabel
    AutoLabel --> AutoPrefix
end
```

**Sources:** [fastapp/apps/config.py L19-L28](/fastapp/apps/config.py#L19-L28)

### Application Discovery Patterns

The framework supports multiple application configuration patterns:

| Pattern | Description | Location | Auto-Discovery |
| --- | --- | --- | --- |
| **Module-based** | App module with optional `apps.py` | `apps/user/` | ✓ |
| **AppConfig subclass** | Custom AppConfig in `apps.py` | `apps/user/apps.py` | ✓ |
| **Explicit class** | Direct AppConfig class reference | `INSTALLED_APPS` | ✗ |

```mermaid
flowchart TD

Entry["INSTALLED_APPS Entry<br>'apps.user'"]
TryModule["Try Module Import<br>cached_import_module()"]
CheckApps["Check for apps.py<br>module_has_submodule()"]
FindAppConfig["Find AppConfig Subclass<br>inspect.getmembers()"]
CreateDefault["Create Default AppConfig<br>AppConfigMeta()"]
TryImportString["Try import_string()<br>Direct class import"]
AppConfigClass["AppConfig Instance"]
ErrorMultiple["RuntimeError"]

FindAppConfig --> AppConfigClass
FindAppConfig --> ErrorMultiple
CreateDefault --> AppConfigClass
TryImportString --> AppConfigClass

subgraph subGraph0 ["Discovery Flow"]
    Entry
    TryModule
    CheckApps
    FindAppConfig
    CreateDefault
    TryImportString
    Entry --> TryModule
    TryModule --> CheckApps
    TryModule --> TryImportString
    CheckApps --> FindAppConfig
    CheckApps --> CreateDefault
    FindAppConfig --> CreateDefault
end
```

**Sources:** [fastapp/apps/config.py L72-L175](/fastapp/apps/config.py#L72-L175)

## Port Management System

Applications with URL patterns are automatically assigned network ports for microservice deployment, with file-based coordination to prevent conflicts.

```mermaid
flowchart TD

HasURLs["has_module('urls')<br>URL patterns detected"]
NotExported["name not in NO_EXPORT_APPS<br>Exportable service"]
EnabledPortMap["ENABLE_PORT_MAP_FILE = True<br>Port mapping enabled"]
FileLock["FileLock<br>PROJECT_NAME_choice_port.lock"]
ReadExisting["read_port_from_json()<br>Check existing assignment"]
FindFree["find_free_port()<br>Avoid conflicts"]
WritePort["write_port_to_json()<br>Persist assignment"]
ManualPort["self.port<br>Explicitly set"]
ExistingPort["Existing JSON<br>Previously assigned"]
AutoPort["Auto-assigned<br>Dynamic allocation"]

EnabledPortMap --> FileLock
ReadExisting --> ExistingPort
FindFree --> AutoPort
AutoPort --> WritePort
ManualPort --> WritePort

subgraph subGraph2 ["Port Sources"]
    ManualPort
    ExistingPort
    AutoPort
end

subgraph subGraph1 ["Port Resolution"]
    FileLock
    ReadExisting
    FindFree
    WritePort
    FileLock --> ReadExisting
    ReadExisting --> FindFree
end

subgraph subGraph0 ["Port Assignment Logic"]
    HasURLs
    NotExported
    EnabledPortMap
    HasURLs --> EnabledPortMap
    NotExported --> EnabledPortMap
end
```

**Sources:** [fastapp/apps/config.py L47-L64](/fastapp/apps/config.py#L47-L64)

 [fastapp/utils/fs.py](/fastapp/utils/fs.py)

 [fastapp/utils/ports.py](/fastapp/utils/ports.py)

## Module Loading and URL Integration

Applications provide modular functionality through dynamic module loading and automatic URL pattern integration with FastAPI routing.

### Dynamic Module Loading

```mermaid
flowchart TD

AppModule["app_module<br>Main app package"]
HasSubmodule["module_has_submodule()<br>Check for submodule"]
CachedImport["cached_import_module()<br>Import with caching"]
Models["models.py<br>BaseModel definitions"]
Views["views.py<br>ViewSet classes"]
URLs["urls.py<br>urlpatterns list"]
Serializers["serializers.py<br>ModelSerializer classes"]
Apps["apps.py<br>AppConfig definitions"]
Internal["internal/views.py<br>Cross-service endpoints"]

CachedImport --> Models
CachedImport --> Views
CachedImport --> URLs
CachedImport --> Serializers
CachedImport --> Apps
CachedImport --> Internal

subgraph subGraph1 ["Common Modules"]
    Models
    Views
    URLs
    Serializers
    Apps
    Internal
end

subgraph subGraph0 ["Module Discovery"]
    AppModule
    HasSubmodule
    CachedImport
    AppModule --> HasSubmodule
    HasSubmodule --> CachedImport
end
```

**Sources:** [fastapp/apps/config.py L177-L183](/fastapp/apps/config.py#L177-L183)

### URL Pattern Loading

The framework automatically loads URL patterns from each application's `urls.py` module:

```mermaid
sequenceDiagram
  participant FastAPI
  participant load_url_module
  participant AppConfig
  participant URLModule
  participant RouterConverter

  FastAPI->>load_url_module: Load app URLs
  load_url_module->>AppConfig: import_module("urls")
  AppConfig->>URLModule: Check urlpatterns attribute
  URLModule->>RouterConverter: router_convert(urlpatterns)
  RouterConverter->>FastAPI: Include converted routers
  note over AppConfig,URLModule: Each app provides urlpatterns
  note over FastAPI,RouterConverter: Converts to FastAPI router format
```

**Sources:** [fastapp/fastapi.py L60-L64](/fastapp/fastapi.py#L60-L64)

## Internal Service Communication

Applications can expose internal endpoints for cross-service communication using the `_cross_service` decorator pattern.

```mermaid
flowchart TD

InternalModule["internal/views.py<br>Cross-service endpoints"]
InspectMembers["inspect.getmembers()<br>Find decorated functions"]
CrossServiceAttr["_cross_service attribute<br>Marker for internal use"]
InternalRouter["APIRouter<br>prefix='/_internal'"]
AddAPIRoute["add_api_route()<br>POST method only"]
WrappedView["cls.wrapped_view<br>Decorated endpoint"]
InternalPrefix["/_internal/<br>Standardized paths"]
InternalTags["tags=['_internal']<br>API documentation"]
PostOnly["methods=['POST']<br>Consistent interface"]

CrossServiceAttr --> InternalRouter
WrappedView --> InternalPrefix

subgraph subGraph2 ["Service Integration"]
    InternalPrefix
    InternalTags
    PostOnly
    InternalPrefix --> InternalTags
    InternalTags --> PostOnly
end

subgraph subGraph1 ["Router Configuration"]
    InternalRouter
    AddAPIRoute
    WrappedView
    InternalRouter --> AddAPIRoute
    AddAPIRoute --> WrappedView
end

subgraph subGraph0 ["Internal Views Discovery"]
    InternalModule
    InspectMembers
    CrossServiceAttr
    InternalModule --> InspectMembers
    InspectMembers --> CrossServiceAttr
end
```

**Sources:** [fastapp/fastapi.py L111-L123](/fastapp/fastapi.py#L111-L123)

## Application Structure Convention

QingKongFramework follows a standardized directory structure for applications:

```go
apps/
├── user/                      # Application package
│   ├── __init__.py           # Package marker
│   ├── apps.py               # AppConfig definition (optional)
│   ├── models.py             # BaseModel classes
│   ├── views.py              # ViewSet classes  
│   ├── serializers.py        # ModelSerializer classes
│   ├── filters.py            # FilterSet classes
│   ├── urls.py               # URL patterns
│   └── internal/             # Internal services (optional)
│       └── views.py          # Cross-service endpoints
├── product/                  # Another application
│   └── ...
└── __init__.py              # Apps package marker
```

### Application Lifecycle Integration

```mermaid
sequenceDiagram
  participant Settings
  participant FastAPI
  participant init_apps
  participant AppConfig
  participant ModuleLoader

  Settings->>FastAPI: INSTALLED_APPS configuration
  FastAPI->>init_apps: Initialize app discovery
  init_apps->>AppConfig: Create app configs
  AppConfig->>ModuleLoader: Load app modules
  ModuleLoader->>AppConfig: Register models, views, URLs
  AppConfig->>FastAPI: Return configured apps
  FastAPI->>FastAPI: Include routers and endpoints
  note over Settings,AppConfig: Application discovery phase
  note over FastAPI,AppConfig: URL loading and router inclusion
```

**Sources:** [fastapp/fastapi.py L79-L126](/fastapp/fastapi.py#L79-L126)