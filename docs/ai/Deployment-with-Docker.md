# Deployment with Docker

> **Relevant source files**
> * [deploy/Dockerfile](/deploy/Dockerfile)
> * [deploy/build.sh](/deploy/build.sh)
> * [deploy/remove_dev_requirements.sh](/deploy/remove_dev_requirements.sh)

This document covers the Docker containerization system for QingKongFramework, including multi-stage build optimization, dependency management, and production deployment configuration. The system provides optimized container builds with asyncmy performance tuning and production-ready dependency filtering.

For server command management, see [Server Commands](Server-Commands.md). For general infrastructure configuration, see [Infrastructure](Infrastructure.md).

## Multi-Stage Build Architecture

The Docker deployment uses a sophisticated multi-stage build process to optimize both build time and final image size while providing performance optimizations for database connectivity.

### Build Pipeline Overview

```mermaid
flowchart TD

BaseBuilder["python:3.12-slim-bookworm"]
MirrorConfig["Configure Chinese Mirrors<br>APT + PyPI"]
DevTools["Install Build Tools<br>gcc, wget, wheel"]
AsyncMyDownload["Download asyncmy-0.2.9<br>Source Package"]
AsyncMyOptimize["Apply Compilation<br>Optimizations"]
AsyncMyBuild["Build Optimized<br>asyncmy Package"]
BaseRuntime["python:3.12-slim-bookworm"]
CopyAsyncMy["Copy Optimized<br>asyncmy Package"]
FilterDeps["Filter Development<br>Dependencies"]
InstallProd["Install Production<br>Dependencies"]
CopyApp["Copy Application<br>Code"]
FinalImage["Production Ready<br>Container"]

AsyncMyBuild --> CopyAsyncMy

subgraph subGraph1 ["Stage 2: Runtime"]
    BaseRuntime
    CopyAsyncMy
    FilterDeps
    InstallProd
    CopyApp
    FinalImage
    BaseRuntime --> CopyAsyncMy
    CopyAsyncMy --> FilterDeps
    FilterDeps --> InstallProd
    InstallProd --> CopyApp
    CopyApp --> FinalImage
end

subgraph subGraph0 ["Stage 1: Builder"]
    BaseBuilder
    MirrorConfig
    DevTools
    AsyncMyDownload
    AsyncMyOptimize
    AsyncMyBuild
    BaseBuilder --> MirrorConfig
    MirrorConfig --> DevTools
    DevTools --> AsyncMyDownload
    AsyncMyDownload --> AsyncMyOptimize
    AsyncMyOptimize --> AsyncMyBuild
end
```

Sources: [deploy/Dockerfile L1-L62](/deploy/Dockerfile#L1-L62)

### AsyncMy Performance Optimization

The build process includes specialized compilation optimizations for the `asyncmy` MySQL driver to improve database performance:

| Optimization Flag | Purpose | Stage |
| --- | --- | --- |
| `-Os` | Size optimization | Compile |
| `-flto` | Link-time optimization | Compile & Link |
| `-ffast-math` | Fast math operations | Compile |
| `-s` | Strip symbols | Link |

The optimization process modifies the asyncmy build configuration dynamically:

```mermaid
flowchart TD

Download["wget asyncmy-0.2.9.tar.gz"]
Extract["tar -xzf asyncmy-0.2.9.tar.gz"]
ModifyBuild["sed -i build.py<br>Add optimization flags"]
CompileInstall["pip install .<br>with optimizations"]

Download --> Extract
Extract --> ModifyBuild
ModifyBuild --> CompileInstall
```

Sources: [deploy/Dockerfile L16-L28](/deploy/Dockerfile#L16-L28)

## Dependency Management

### Development Dependency Filtering

The build process uses a custom script to separate production dependencies from development dependencies, reducing final image size and potential security surface.

```mermaid
flowchart TD

FullRequirements["requirements.txt<br>Full Dependencies"]
FilterScript["remove_dev_requirements.sh<br>Filter Script"]
CleanRequirements["requirements.txt.clean<br>Production Only"]
PipInstall["pip install -r requirements.txt.clean<br>Production Dependencies"]
AwkProcess["awk '/^# Dev/ {exit} {print}'<br>Stop at Dev marker"]

FullRequirements --> FilterScript
FilterScript --> CleanRequirements
CleanRequirements --> PipInstall

subgraph subGraph0 ["Filter Logic"]
    FilterScript
    AwkProcess
    FilterScript --> AwkProcess
end
```

The filtering script uses a simple marker-based approach where development dependencies are separated by a `# Dev` comment line.

Sources: [deploy/remove_dev_requirements.sh L1-L21](/deploy/remove_dev_requirements.sh#L1-L21)

 [deploy/Dockerfile L48-L54](/deploy/Dockerfile#L48-L54)

### Production Package Installation

The production stage installs only filtered dependencies with cache optimization:

| Step | Command | Purpose |
| --- | --- | --- |
| Filter | `remove-dev-requirements` | Extract production deps |
| Install | `pip install --no-cache-dir` | Install without cache |
| Cleanup | `find ... -name '__pycache__' -exec rm -r {} +` | Remove Python cache |

Sources: [deploy/Dockerfile L51-L54](/deploy/Dockerfile#L51-L54)

## Container Structure

### Application Layout

The final container follows a standardized directory structure:

```mermaid
flowchart TD

SitePackages["/usr/local/lib/python3.12/site-packages/"]
OptimizedAsyncMy["asyncmy/<br>Optimized Build"]
ProductionDeps["Production Dependencies<br>Filtered Requirements"]
AppRoot["/app/<br>WORKDIR & PYTHONPATH"]
FastApp["/app/fastapp/<br>Framework Core"]
Common["/app/common/<br>Shared Utilities"]
ManagePy["/app/manage.py<br>CLI Entry Point"]

AppRoot --> FastApp
AppRoot --> Common
AppRoot --> ManagePy

subgraph subGraph0 ["Application Code"]
    FastApp
    Common
    ManagePy
end

subgraph subGraph1 ["Python Environment"]
    SitePackages
    OptimizedAsyncMy
    ProductionDeps
    SitePackages --> OptimizedAsyncMy
    SitePackages --> ProductionDeps
end
```

Sources: [deploy/Dockerfile L42-L59](/deploy/Dockerfile#L42-L59)

### Runtime Configuration

The container is configured for production deployment with:

* **Working Directory**: `/app/` with `PYTHONPATH=/app`
* **Timezone**: Asia/Shanghai (`/usr/share/zoneinfo/Asia/Shanghai`)
* **Exposed Port**: 8000
* **Default Command**: `python manage.py about`

Sources: [deploy/Dockerfile L33-L62](/deploy/Dockerfile#L33-L62)

## Build Process

### Build Script Integration

The build process is orchestrated through a simple shell script that provides consistent tagging:

```mermaid
flowchart TD

BuildScript["build.sh"]
DockerBuild["docker build<br>-f deploy/Dockerfile"]
Tags["qingkong_framework:latest-py3.12<br>fastapp:latest-py3.12"]

BuildScript --> DockerBuild
DockerBuild --> Tags
```

The build script creates two tags for the same image, providing flexibility for different naming conventions.

Sources: [deploy/build.sh L1](/deploy/build.sh#L1-L1)

### Image Optimization Features

The Docker build includes several optimization strategies:

| Feature | Implementation | Benefit |
| --- | --- | --- |
| Multi-stage build | Separate builder/runtime stages | Smaller final image |
| asyncmy optimization | Custom compilation flags | Better DB performance |
| Cache cleanup | Remove `__pycache__` directories | Reduced image size |
| Dev dependency filtering | Custom script filtering | Security & size reduction |
| Chinese mirror configuration | APT & PyPI mirror setup | Faster builds in China |

Sources: [deploy/Dockerfile L1-L62](/deploy/Dockerfile#L1-L62)

 [deploy/remove_dev_requirements.sh L1-L21](/deploy/remove_dev_requirements.sh#L1-L21)

## Deployment Configuration

The container is designed for production deployment with the QingKongFramework CLI system. The default command runs `manage.py about`, but in production environments, this would typically be overridden with server commands like:

* `python manage.py runserver-aio` for single-process deployment
* `python manage.py runserver` for multi-service deployment
* `python manage.py gateway` for API gateway functionality

The optimized asyncmy driver provides enhanced performance for database operations, particularly beneficial for high-throughput async workloads typical in QingKongFramework applications.

Sources: [deploy/Dockerfile L60-L62](/deploy/Dockerfile#L60-L62)