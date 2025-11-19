# Testing and Build Process

> **Relevant source files**
> * [Readme.md](/Readme.md)
> * [fastapp/commands/__init__.py](/fastapp/commands/__init__.py)
> * [fastapp/commands/decorators.py](/fastapp/commands/decorators.py)
> * [fastapp/commands/server.py](/fastapp/commands/server.py)
> * [fastapp/commands/tests.py](/fastapp/commands/tests.py)
> * [fastapp/misc/serve.py](/fastapp/misc/serve.py)
> * [fastapp/serve/aio.py](/fastapp/serve/aio.py)

This document covers the testing framework, build processes, and performance optimization tools in QingKongFramework. It explains how to run tests across applications, build optimized distributions, and manage development/production servers with performance enhancements.

For information about CLI commands in general, see [Command Line Interface](Command-Line-Interface.md). For deployment configurations, see [Deployment with Docker](Deployment-with-Docker.md).

## Testing Framework

QingKongFramework provides a comprehensive testing system that can discover and execute test functions across all installed applications. The test runner supports both synchronous and asynchronous test functions and provides filtering capabilities.

### Test Discovery and Execution

The testing system automatically discovers test functions using Python's module inspection capabilities:

```mermaid
flowchart TD

run_tests["run_tests command"]
async_run_tests["async_run_tests function"]
apps["installed_apps: Apps"]
app_configs["app_configs.items()"]
has_tests["has_module('tests')"]
import_tests["app_config.import_module('tests')"]
skip["Skip application"]
walk_packages["pkgutil.walk_packages"]
inspect_members["inspect.getmembers"]
test_functions["Functions starting with 'test_' or 'perf_'"]
is_coroutine["asyncio.iscoroutinefunction"]
await_test["await obj()"]
sync_test["obj()"]

run_tests --> async_run_tests
async_run_tests --> apps
apps --> app_configs
app_configs --> has_tests
has_tests --> import_tests
has_tests --> skip
import_tests --> walk_packages
walk_packages --> inspect_members
inspect_members --> test_functions
test_functions --> is_coroutine
is_coroutine --> await_test
is_coroutine --> sync_test
```

Sources: [fastapp/commands/tests.py L12-L43](/fastapp/commands/tests.py#L12-L43)

### Test Command Interface

The test runner provides filtering options for targeted testing:

| Parameter | Type | Description |
| --- | --- | --- |
| `--apps` | multiple | Specific application labels to test |
| `--cases` | multiple | Specific test function names to execute |

The command uses the `@async_init_fastapp` decorator to ensure proper framework initialization before running tests:

* Initializes all installed apps
* Sets up cache connections
* Establishes database connections with Tortoise ORM
* Ensures proper cleanup of connections after test completion

Sources: [fastapp/commands/tests.py L45-L54](/fastapp/commands/tests.py#L45-L54)

 [fastapp/commands/decorators.py L10-L24](/fastapp/commands/decorators.py#L10-L24)

## Build Processes

QingKongFramework supports two distinct build approaches optimized for different use cases:

### Build Configuration Matrix

```mermaid
flowchart TD

source["Source Code"]
nuitka_build["Nuitka Build"]
pure_build["Pure Python Build"]
nuitka_wheel["Compiled Wheel<br>python -m build"]
pure_wheel["Pure Wheel<br>setup-pure.py bdist_wheel"]
performance["High Performance<br>Compiled Extensions"]
compatibility["Maximum Compatibility<br>Pure Python"]

source --> nuitka_build
source --> pure_build
nuitka_build --> nuitka_wheel
pure_build --> pure_wheel
nuitka_wheel --> performance
pure_wheel --> compatibility
```

Sources: [Readme.md L1-L15](/Readme.md#L1-L15)

### Nuitka Build Process

The Nuitka build process creates optimized compiled extensions, particularly beneficial for JSON processing performance:

* **Command**: `python -m build`
* **Optimizations**: Leverages orjson==3.10.15 for accelerated JSON operations
* **Target**: Production deployments requiring maximum performance

### Pure Python Build Process

The pure Python build maintains maximum compatibility across environments:

* **Command**: `python setup-pure.py bdist_wheel`
* **Benefits**: No compiled dependencies, easier deployment
* **Target**: Development environments or constrained deployment scenarios

## Development Server Architecture

The framework provides multiple server configurations for different development and production scenarios:

### Server Command Options

```mermaid
flowchart TD

runserver["runserver<br>Multi-app deployment"]
runserver_aio["runserver-aio<br>All-in-one mode"]
gateway["gateway<br>API gateway/proxy"]
serve_static["serve_static<br>Static file server"]
serve_apps["serve_apps()<br>Multi-process apps"]
serve_app["serve_app()<br>Single app process"]
serve_app_aio["serve_app_aio()<br>Combined routing"]
run_gateway["run_gateway()<br>Upstream routing"]
multiprocessing["multiprocessing.Process"]
signal_handling["Signal handlers<br>SIGINT, SIGTERM, SIGQUIT"]
uvicorn_patches["Uvicorn patches<br>WatchFilesReload, subprocess"]

runserver --> serve_apps
runserver --> serve_app
runserver_aio --> serve_app_aio
gateway --> run_gateway
serve_apps --> multiprocessing
serve_apps --> signal_handling
serve_app --> uvicorn_patches

subgraph subGraph2 ["Process Management"]
    multiprocessing
    signal_handling
    uvicorn_patches
end

subgraph subGraph1 ["Serving Functions"]
    serve_apps
    serve_app
    serve_app_aio
    run_gateway
end

subgraph subGraph0 ["Server Commands"]
    runserver
    runserver_aio
    gateway
    serve_static
end
```

Sources: [fastapp/commands/server.py L10-L52](/fastapp/commands/server.py#L10-L52)

 [fastapp/misc/serve.py L29-L135](/fastapp/misc/serve.py#L29-L135)

### Performance Optimizations

The server implementation includes several performance enhancements:

#### Uvloop Integration

The framework automatically detects and installs uvloop for improved async performance:

```python
# uvloop installation with optional warning
if uvloop is not None:
    uvloop.install()
    if settings.UVLOOP_WARNING:
        print("[uvloop installed]")
```

#### Multi-Process Architecture

For production deployments, the framework supports multi-process serving with automatic process management:

* **Port Validation**: Prevents port conflicts between applications
* **Process Monitoring**: Tracks all spawned processes for clean shutdown
* **Signal Handling**: Graceful termination on SIGINT/SIGTERM/SIGQUIT
* **Daemon Management**: Proper cleanup of child processes

Sources: [fastapp/misc/serve.py L80-L123](/fastapp/misc/serve.py#L80-L123)

### Development Server Features

| Server Mode | Use Case | Key Features |
| --- | --- | --- |
| `runserver` | Multi-app development | Individual app processes, port isolation |
| `runserver-aio` | Single-process development | Combined routing, simplified debugging |
| `gateway` | API gateway/proxy | Upstream routing, load balancing |
| `serve_static` | Frontend development | Static files + API proxying |

#### Hot Reload Configuration

Development servers support hot reload with intelligent directory watching:

```mermaid
flowchart TD

reload_dirs["Reload Directories"]
app_dir["Application Directory<br>inspect.getfile(app_config)"]
fastapp_dir["FastApp Framework<br>fastapp/ directory"]
common_dir["Common Settings<br>common/ directory"]
WatchFilesReload["WatchFilesReload patch"]
uvicorn_reload["Uvicorn Auto-reload"]

reload_dirs --> app_dir
reload_dirs --> fastapp_dir
reload_dirs --> common_dir
app_dir --> WatchFilesReload
fastapp_dir --> WatchFilesReload
common_dir --> WatchFilesReload
WatchFilesReload --> uvicorn_reload
```

Sources: [fastapp/misc/serve.py L54-L61](/fastapp/misc/serve.py#L54-L61)

## Process Management and Monitoring

### Multi-Process Server Management

The framework implements robust process management for production deployments:

#### Process Lifecycle

```mermaid
stateDiagram-v2
    [*] --> StartupValidation : "Validate app configs"
    StartupValidation --> PortCheck : "Validate app configs"
    PortCheck --> ProcessSpawn : "No conflicts"
    PortCheck --> Error : "Port duplicate"
    ProcessSpawn --> ProcessMonitoring : "Create processes"
    ProcessMonitoring --> SignalWait : "Register handlers"
    SignalWait --> GracefulShutdown : "Receive signal"
    GracefulShutdown --> ProcessTermination : "Terminate all"
    ProcessTermination --> [*] : "Clean exit"
    Error --> [*] : "Exit with error"
```

#### Signal Handling Implementation

The server implements comprehensive signal handling for clean shutdown:

* **SIGINT**: Keyboard interrupt (Ctrl+C)
* **SIGTERM**: Termination request
* **SIGQUIT**: Quit signal
* **Process Tracking**: Maintains list of active processes for cleanup

Sources: [fastapp/misc/serve.py L65-L122](/fastapp/misc/serve.py#L65-L122)

### Logging and Debugging Configuration

Each server mode includes customized logging configuration:

* **Per-App Labeling**: Log messages tagged with application labels
* **Log Level Control**: Configurable verbosity levels
* **Template System**: Consistent logging format across services
* **Debug Mode**: Enhanced error reporting for development

Sources: [fastapp/misc/serve.py L43-L46](/fastapp/misc/serve.py#L43-L46)