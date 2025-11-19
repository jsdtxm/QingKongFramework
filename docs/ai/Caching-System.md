# Caching System

> **Relevant source files**
> * [fastapp/cache/__init__.py](/fastapp/cache/__init__.py)
> * [fastapp/cache/base.py](/fastapp/cache/base.py)
> * [fastapp/cache/disk.py](/fastapp/cache/disk.py)
> * [fastapp/cache/states.py](/fastapp/cache/states.py)
> * [fastapp/initialize/cache.py](/fastapp/initialize/cache.py)

The caching system provides a multi-backend cache abstraction layer that supports Redis, disk-based caching, and PostgreSQL backends. It integrates with FastAPI through the `fastapi-cache` library and provides both asynchronous and synchronous interfaces for cache operations.

This system handles cache configuration, connection management, and provides a unified API across different storage backends. For database-specific optimizations and schema management, see [Database Management](Database-Management.md).

## Architecture Overview

The caching system follows a layered architecture with pluggable backends, centralized connection management, and a unified cache interface.

```mermaid
flowchart TD

App["FastAPI Application"]
ViewSets["ViewSets/Controllers"]
LazyCache["LazyCache Proxy"]
FastAPICacheWrapper["FastAPICacheWrapper"]
CacheRegistry["caches dict"]
RedisBackend["RedisCache Backend"]
DiskBackend["DiskCacheBackend"]
PostgresBackend["PostgresBackend"]
Redis["Redis Server"]
DiskCache["diskcache.Cache"]
PostgreSQL["PostgreSQL Database"]
ConnectionsDict["connections dict"]
RedisConn["aioredis.from_url()"]
DiskConn["DiskCacheBackend instance"]
PostgresConn["asyncpg.connect()"]

App --> LazyCache
ViewSets --> CacheRegistry
FastAPICacheWrapper --> RedisBackend
FastAPICacheWrapper --> DiskBackend
FastAPICacheWrapper --> PostgresBackend
RedisBackend --> RedisConn
DiskBackend --> DiskConn
PostgresBackend --> PostgresConn
RedisConn --> Redis
DiskConn --> DiskCache
PostgresConn --> PostgreSQL

subgraph subGraph4 ["Connection Management"]
    ConnectionsDict
    RedisConn
    DiskConn
    PostgresConn
    ConnectionsDict --> RedisConn
    ConnectionsDict --> DiskConn
    ConnectionsDict --> PostgresConn
end

subgraph subGraph3 ["Storage Systems"]
    Redis
    DiskCache
    PostgreSQL
end

subgraph subGraph2 ["Backend Implementations"]
    RedisBackend
    DiskBackend
    PostgresBackend
end

subgraph subGraph1 ["Cache Interface Layer"]
    LazyCache
    FastAPICacheWrapper
    CacheRegistry
    LazyCache --> FastAPICacheWrapper
    CacheRegistry --> FastAPICacheWrapper
end

subgraph subGraph0 ["Application Layer"]
    App
    ViewSets
end
```

Sources: [fastapp/initialize/cache.py L1-L61](/fastapp/initialize/cache.py#L1-L61)

 [fastapp/cache/states.py L1-L22](/fastapp/cache/states.py#L1-L22)

 [fastapp/cache/__init__.py L1-L10](/fastapp/cache/__init__.py#L1-L10)

## Backend Types and Configuration

The system supports three primary cache backends, each with different use cases and configuration requirements.

### Supported Cache Backends

| Backend | Class | Use Case | Configuration Keys |
| --- | --- | --- | --- |
| Redis | `RedisCache` | Distributed caching, high performance | `LOCATION` (Redis URL) |
| Disk | `DiskCacheBackend` | Local file-based caching | `DIRECTORY`, `TIMEOUT`, `DISK`, `OPTIONS` |
| PostgreSQL | `PostgresBackend` | Database-backed caching | `LOCATION` (DSN) |

### Backend-Specific Features

```mermaid
flowchart TD

RedisAsync["Async Operations"]
RedisDistributed["Distributed Cache"]
RedisExpiry["TTL Support"]
DiskLocal["Local Storage"]
DiskSync["Sync/Async Bridge"]
DiskCustomizable["Configurable Disk Types"]
PostgresTransactional["Transactional"]
PostgresQuery["SQL Queryable"]
PostgresPersistent["Persistent Storage"]
RedisCache["RedisCache"]
DiskCacheBackend["DiskCacheBackend"]
PostgresBackend["PostgresBackend"]

RedisCache --> RedisAsync
RedisCache --> RedisDistributed
RedisCache --> RedisExpiry
DiskCacheBackend --> DiskLocal
DiskCacheBackend --> DiskSync
DiskCacheBackend --> DiskCustomizable
PostgresBackend --> PostgresTransactional
PostgresBackend --> PostgresQuery
PostgresBackend --> PostgresPersistent

subgraph subGraph2 ["PostgresBackend Features"]
    PostgresTransactional
    PostgresQuery
    PostgresPersistent
end

subgraph subGraph1 ["DiskCacheBackend Features"]
    DiskLocal
    DiskSync
    DiskCustomizable
end

subgraph subGraph0 ["RedisCache Features"]
    RedisAsync
    RedisDistributed
    RedisExpiry
end
```

Sources: [fastapp/initialize/cache.py L20-L38](/fastapp/initialize/cache.py#L20-L38)

 [fastapp/cache/disk.py L10-L27](/fastapp/cache/disk.py#L10-L27)

## Cache Initialization Process

The cache initialization follows a configuration-driven approach that sets up connections and cache instances for each configured backend.

### Initialization Flow

```mermaid
sequenceDiagram
  participant settings.CACHES
  participant init_cache()
  participant import_string()
  participant connections dict
  participant caches dict
  participant FastAPICacheWrapper

  settings.CACHES->>init_cache(): "Cache configurations"
  loop ["RedisCache backend"]
    init_cache()->>init_cache(): "Extract backend type"
    init_cache()->>import_string(): "aioredis.from_url()"
    import_string()-->>init_cache(): "Redis connection"
    init_cache()->>import_string(): "DiskCacheBackend()"
    import_string()-->>init_cache(): "Disk cache instance"
    init_cache()->>import_string(): "asyncpg.connect()"
    import_string()-->>init_cache(): "PostgreSQL connection"
    init_cache()->>connections dict: "Store connection"
    init_cache()->>caches dict: "Store backend directly"
    init_cache()->>FastAPICacheWrapper: "Create wrapper class"
    FastAPICacheWrapper->>import_string(): "Load backend class"
    import_string()-->>FastAPICacheWrapper: "Backend instance"
    FastAPICacheWrapper->>FastAPICacheWrapper: "Initialize with connection"
    init_cache()->>caches dict: "Store wrapper"
  end
```

Sources: [fastapp/initialize/cache.py L16-L61](/fastapp/initialize/cache.py#L16-L61)

## Base Cache Interface

The `BaseCache` class defines the standard interface that all cache backends must implement, providing both async and sync operations.

### Core Cache Operations

The cache interface provides these primary operation categories:

| Operation Type | Async Methods | Sync Methods | Purpose |
| --- | --- | --- | --- |
| Basic CRUD | `get()`, `set()`, `add()`, `delete()` | `sync_get()`, `sync_set()` | Basic key-value operations |
| Batch Operations | `get_many()`, `set_many()`, `delete_many()` | - | Bulk operations for efficiency |
| Utility | `touch()`, `clear()`, `has_key()` | - | Cache management |
| Arithmetic | `incr()`, `decr()` | - | Numeric value manipulation |
| Advanced | `get_or_set()`, `incr_version()` | - | Composite operations |

### Key Generation and Versioning

The cache system includes sophisticated key management:

```mermaid
flowchart TD

RawKey["Raw Key"]
KeyFunc["key_func()"]
KeyPrefix["KEY_PREFIX"]
Version["VERSION"]
FinalKey["Final Cache Key"]
DefaultKeyFunc["default_key_func()"]
CustomKeyFunc["Custom Key Function"]
ImportString["import_string()"]
CacheKey["prefix:version:key"]

DefaultKeyFunc --> KeyFunc
CustomKeyFunc --> KeyFunc
FinalKey --> CacheKey

subgraph subGraph1 ["Key Components"]
    DefaultKeyFunc
    CustomKeyFunc
    ImportString
    ImportString --> CustomKeyFunc
end

subgraph subGraph0 ["Key Generation Process"]
    RawKey
    KeyFunc
    KeyPrefix
    Version
    FinalKey
    RawKey --> KeyFunc
    KeyPrefix --> KeyFunc
    Version --> KeyFunc
    KeyFunc --> FinalKey
end
```

Sources: [fastapp/cache/base.py L10-L42](/fastapp/cache/base.py#L10-L42)

 [fastapp/cache/base.py L94-L105](/fastapp/cache/base.py#L94-L105)

## Disk Cache Backend Implementation

The `DiskCacheBackend` provides a local file-based cache using the `diskcache` library with async-to-sync bridging.

### Async-to-Sync Bridge Pattern

```mermaid
flowchart TD

AsyncGet["async get()"]
AsyncSet["async set()"]
AsyncAdd["async add()"]
AsyncDelete["async delete()"]
RunInExecutor["loop.run_in_executor()"]
EventLoop["asyncio.get_running_loop()"]
SyncGet["_cache.get()"]
SyncSet["_cache.set()"]
SyncAdd["_cache.add()"]
SyncDelete["_cache.delete()"]
DiskCacheLib["diskcache.Cache"]
FileSystem["Local File System"]

AsyncGet --> RunInExecutor
AsyncSet --> RunInExecutor
AsyncAdd --> RunInExecutor
AsyncDelete --> RunInExecutor
RunInExecutor --> SyncGet
RunInExecutor --> SyncSet
RunInExecutor --> SyncAdd
RunInExecutor --> SyncDelete
SyncGet --> DiskCacheLib
SyncSet --> DiskCacheLib
SyncAdd --> DiskCacheLib
SyncDelete --> DiskCacheLib

subgraph subGraph3 ["Disk Storage"]
    DiskCacheLib
    FileSystem
    DiskCacheLib --> FileSystem
end

subgraph subGraph2 ["Sync Implementation"]
    SyncGet
    SyncSet
    SyncAdd
    SyncDelete
end

subgraph subGraph1 ["Event Loop Bridge"]
    RunInExecutor
    EventLoop
end

subgraph subGraph0 ["Async Interface"]
    AsyncGet
    AsyncSet
    AsyncAdd
    AsyncDelete
end
```

### Configuration Options

The `DiskCacheBackend` supports extensive configuration through the `OPTIONS` parameter:

* **directory**: Storage directory path
* **timeout**: Default timeout for cache entries
* **disk**: Disk implementation class (e.g., `diskcache.Disk`)
* **OPTIONS**: Additional parameters passed to the underlying `diskcache.Cache`

Sources: [fastapp/cache/disk.py L10-L72](/fastapp/cache/disk.py#L10-L72)

 [fastapp/cache/base.py L56-L81](/fastapp/cache/base.py#L56-L81)

## Cache Access Patterns

The system provides multiple ways to access cache instances depending on the use case.

### Global Cache Access

```mermaid
flowchart TD

LazyCache["LazyCache instance"]
DefaultCache["cache = LazyCache()"]
CachesDict["caches['alias']"]
ConnectionsDict["connections['alias']"]
GetAttr["getattr()"]
CacheProperty["cache property"]
FastAPICacheWrapper["FastAPICacheWrapper"]
BackendConnection["BackendConnection"]

LazyCache --> CacheProperty
CacheProperty --> CachesDict
CachesDict --> FastAPICacheWrapper
ConnectionsDict --> BackendConnection

subgraph subGraph2 ["Proxy Behavior"]
    GetAttr
    CacheProperty
    GetAttr --> CacheProperty
end

subgraph subGraph1 ["Named Cache Access"]
    CachesDict
    ConnectionsDict
end

subgraph subGraph0 ["Global Access"]
    LazyCache
    DefaultCache
    DefaultCache --> LazyCache
end
```

### FastAPICache Integration

The `FastAPICacheWrapper` extends `FastAPICache` to provide direct access to backend methods:

* Intercepts method calls for `get`, `set`, `sync_get`, `sync_set`
* Forwards calls directly to the backend if available
* Raises `AttributeError` for unavailable methods

Sources: [fastapp/cache/states.py L12-L22](/fastapp/cache/states.py#L12-L22)

 [fastapp/initialize/cache.py L8-L13](/fastapp/initialize/cache.py#L8-L13)

## Configuration and Settings

Cache backends are configured through the `settings.CACHES` dictionary, with each entry representing a named cache configuration.

### Example Configuration Structure

```css
# Example cache configuration
CACHES = {
    "default": {
        "BACKEND": "fastapp.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/0"
    },
    "disk_cache": {
        "BACKEND": "fastapp.cache.DiskCacheBackend",
        "DIRECTORY": "/tmp/cache",
        "TIMEOUT": 3600,
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
            "CULL_FREQUENCY": 3
        }
    },
    "postgres_cache": {
        "BACKEND": "fastapp.cache.PostgresBackend",
        "LOCATION": "postgresql://user:pass@localhost/db"
    }
}
```

The initialization process uses `import_string()` to dynamically load backend classes and creates appropriate connection objects based on the backend type.

Sources: [fastapp/initialize/cache.py L17-L40](/fastapp/initialize/cache.py#L17-L40)

 [fastapp/cache/base.py L56-L81](/fastapp/cache/base.py#L56-L81)