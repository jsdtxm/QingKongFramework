# Pagination and Permissions

> **Relevant source files**
> * [fastapp/paginate/base.py](/fastapp/paginate/base.py)
> * [fastapp/paginate/pro.py](/fastapp/paginate/pro.py)
> * [fastapp/permissions/base.py](/fastapp/permissions/base.py)
> * [fastapp/permissions/role.py](/fastapp/permissions/role.py)
> * [fastapp/views/viewsets.py](/fastapp/views/viewsets.py)

This document covers the pagination and permission systems used by ViewSets in QingKongFramework. These systems provide essential functionality for controlling access to API endpoints and managing large dataset responses.

For information about ViewSet CRUD operations, see [ViewSets and CRUD Operations](ViewSets-and-CRUD-Operations.md). For authentication mechanisms and user management, see [Authentication and Authorization](Authentication-and-Authorization.md).

## Permission System

The framework provides a flexible permission system that allows fine-grained access control at both the view level and object level. The system supports logical operations and composable permission classes.

### Permission Class Hierarchy

```mermaid
classDiagram
    class BasePermission {
        +has_permission(request, view) : bool
        +has_object_permission(request, view, obj) : bool
    }
    class OperationHolderMixin {
        +and(other) : OperandHolder
        +or(other) : OperandHolder
        +invert() : SingleOperandHolder
    }
    class AND {
        -op1: BasePermission
        -op2: BasePermission
        +has_permission(request, view) : bool
        +has_object_permission(request, view, obj) : bool
    }
    class OR {
        -op1: BasePermission
        -op2: BasePermission
        +has_permission(request, view) : bool
        +has_object_permission(request, view, obj) : bool
    }
    class NOT {
        -op1: BasePermission
        +has_permission(request, view) : bool
        +has_object_permission(request, view, obj) : bool
    }
    class AllowAny {
        +has_permission(request, view) : bool
    }
    class IsAuthenticated {
        +has_permission(request, view) : bool
    }
    class IsAdminUser {
        +has_permission(request, view) : bool
    }
    class IsAuthenticatedOrReadOnly {
        +has_permission(request, view) : bool
    }
    BasePermission <|-- AllowAny : uses
    BasePermission <|-- IsAuthenticated : uses
    BasePermission <|-- IsAdminUser : uses
    BasePermission <|-- IsAuthenticatedOrReadOnly
    OperationHolderMixin <|-- BasePermission
    AND <.. BasePermission
    OR <.. BasePermission
    NOT <.. BasePermission
```

Sources: [fastapp/permissions/base.py L107-L123](/fastapp/permissions/base.py#L107-L123)

 [fastapp/permissions/role.py L5-L51](/fastapp/permissions/role.py#L5-L51)

### Built-in Permission Classes

| Permission Class | Description | Usage |
| --- | --- | --- |
| `AllowAny` | Grants access to all requests | Public endpoints |
| `IsAuthenticated` | Requires authenticated user with active status | Protected endpoints |
| `IsAdminUser` | Requires authenticated superuser | Admin-only endpoints |
| `IsAuthenticatedOrReadOnly` | Allows read access to all, write access to authenticated users | Mixed access endpoints |

Sources: [fastapp/permissions/role.py L5-L51](/fastapp/permissions/role.py#L5-L51)

### Permission Composition

The framework supports logical composition of permissions using Python operators:

* **AND (`&`)**: Both permissions must pass
* **OR (`|`)**: Either permission must pass
* **NOT (`~`)**: Permission must fail

```markdown
# Example: Admin or authenticated read-only access
permission = IsAdminUser | (IsAuthenticated & IsReadOnly)
```

Sources: [fastapp/permissions/base.py L6-L21](/fastapp/permissions/base.py#L6-L21)

 [fastapp/permissions/base.py L56-L101](/fastapp/permissions/base.py#L56-L101)

## Pagination System

The pagination system provides multiple backends for handling large datasets with consistent response formats and configurable parameters.

### Pagination Architecture

```mermaid
flowchart TD

GenericAPIView["GenericAPIView"]
paginate_queryset["paginate_queryset()"]
BasePaginate["BasePaginate.paginate_queryset()"]
BaseFilter["BaseFilter params"]
get_limit_offset["get_limit_offset()"]
queryset_slice["queryset.offset().limit()"]
get_paginated_response["get_paginated_response()"]
JSONResponse["JSONResponse"]
ProPaginate["ProPaginate"]
ProTableFilter["ProTableFilter"]
DEFAULT_PAGINATION_CLASS["DEFAULT_PAGINATION_CLASS"]
pagination_class["view.pagination_class"]

BasePaginate --> ProPaginate
BaseFilter --> ProTableFilter
pagination_class --> BasePaginate

subgraph Configuration ["Configuration"]
    DEFAULT_PAGINATION_CLASS
    pagination_class
    DEFAULT_PAGINATION_CLASS --> pagination_class
end

subgraph subGraph1 ["Pagination Backends"]
    ProPaginate
    ProTableFilter
end

subgraph subGraph0 ["Pagination Flow"]
    GenericAPIView
    paginate_queryset
    BasePaginate
    BaseFilter
    get_limit_offset
    queryset_slice
    get_paginated_response
    JSONResponse
    GenericAPIView --> paginate_queryset
    paginate_queryset --> BasePaginate
    BasePaginate --> BaseFilter
    BasePaginate --> get_limit_offset
    get_limit_offset --> queryset_slice
    queryset_slice --> get_paginated_response
    get_paginated_response --> JSONResponse
end
```

Sources: [fastapp/views/viewsets.py L449-L475](/fastapp/views/viewsets.py#L449-L475)

 [fastapp/paginate/base.py L14-L32](/fastapp/paginate/base.py#L14-L32)

 [fastapp/paginate/pro.py L30-L36](/fastapp/paginate/pro.py#L30-L36)

### Pagination Parameters

| Backend | Parameters | Default Values | Response Format |
| --- | --- | --- | --- |
| `BasePaginate` | `page_size`, `current` | 20, 1 | `{"data": [...], "total": N}` |
| `ProPaginate` | `pageSize`, `current` | 20, 1 | `{"data": [...], "total": N, "success": true}` |

Sources: [fastapp/paginate/base.py L9-L12](/fastapp/paginate/base.py#L9-L12)

 [fastapp/paginate/pro.py L8-L11](/fastapp/paginate/pro.py#L8-L11)

### Custom Pagination Backend

To create a custom pagination backend, extend `BasePaginate` and implement the required methods:

```python
class CustomPaginate(BasePaginate):
    params_model = CustomFilter
    
    @classmethod
    async def paginate_queryset(cls, queryset, request, view):
        # Custom pagination logic
        pass
    
    @classmethod
    def get_paginated_response(cls, data, total=None):
        # Custom response format
        pass
```

Sources: [fastapp/paginate/base.py L14-L32](/fastapp/paginate/base.py#L14-L32)

## ViewSet Integration

ViewSets integrate both permission and pagination systems through the `GenericAPIView` base class, providing a unified interface for API endpoints.

### Permission Flow in ViewSets

```mermaid
sequenceDiagram
  participant Request
  participant APIView
  participant PermissionClass
  participant ViewMethod

  Request->>APIView: "HTTP Request"
  APIView->>APIView: "check_permissions(request)"
  loop ["Permission denied"]
    APIView->>PermissionClass: "has_permission(request, view)"
    PermissionClass-->>APIView: "True/False"
    APIView->>APIView: "permission_denied()"
    APIView-->>Request: "403 Forbidden / 401 Unauthorized"
    APIView->>ViewMethod: "dispatch to action method"
    ViewMethod->>APIView: "check_object_permissions(request, obj)"
    APIView->>PermissionClass: "has_object_permission(request, view, obj)"
    PermissionClass-->>APIView: "True/False"
    APIView->>APIView: "permission_denied()"
    APIView-->>Request: "403 Forbidden"
  end
  ViewMethod-->>Request: "Success Response"
```

Sources: [fastapp/views/viewsets.py L197-L239](/fastapp/views/viewsets.py#L197-L239)

### Pagination Flow in ViewSets

```mermaid
sequenceDiagram
  participant ListAction
  participant GenericAPIView
  participant PaginationClass
  participant QuerySet
  participant Response

  ListAction->>GenericAPIView: "get_queryset()"
  GenericAPIView-->>ListAction: "queryset"
  ListAction->>GenericAPIView: "paginate_queryset(queryset)"
  GenericAPIView->>PaginationClass: "paginate_queryset(queryset, request, view)"
  PaginationClass->>QuerySet: "count()"
  QuerySet-->>PaginationClass: "total_count"
  PaginationClass->>QuerySet: "offset(N).limit(M)"
  QuerySet-->>PaginationClass: "page_data"
  PaginationClass-->>GenericAPIView: "BasePaginate instance"
  GenericAPIView-->>ListAction: "paginated_queryset or None"
  loop ["Pagination enabled"]
    ListAction->>GenericAPIView: "get_paginated_response(data)"
    GenericAPIView->>PaginationClass: "get_paginated_response(data, total)"
    PaginationClass-->>Response: "JSONResponse with pagination metadata"
    ListAction-->>Response: "JSONResponse(data)"
  end
```

Sources: [fastapp/views/viewsets.py L456-L475](/fastapp/views/viewsets.py#L456-L475)

### ViewSet Configuration

ViewSets can configure permissions and pagination through class attributes:

| Attribute | Purpose | Default Value |
| --- | --- | --- |
| `permission_classes` | List of permission class references | `["fastapp.permissions.AllowAny"]` |
| `pagination_class` | Pagination backend class reference | `settings.DEFAULT_PAGINATION_CLASS` |

Sources: [fastapp/views/viewsets.py L44-L49](/fastapp/views/viewsets.py#L44-L49)

 [fastapp/views/viewsets.py L198](/fastapp/views/viewsets.py#L198-L198)

 [fastapp/views/viewsets.py L276](/fastapp/views/viewsets.py#L276-L276)

## Configuration and Defaults

### Global Configuration

The framework provides global defaults that can be overridden at the application level:

```
DEFAULTS = {
    "DEFAULT_PERMISSION_CLASSES": [
        "fastapp.permissions.AllowAny",
    ],
    "DEFAULT_PAGINATION_CLASS": settings.DEFAULT_PAGINATION_CLASS,
}
```

Sources: [fastapp/views/viewsets.py L44-L49](/fastapp/views/viewsets.py#L44-L49)

### ViewSet-Level Overrides

Individual ViewSets can override the global defaults:

```python
class MyViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = ProPaginate
    
    # Custom permission logic
    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        return super().get_permissions()
```

Sources: [fastapp/views/viewsets.py L208-L212](/fastapp/views/viewsets.py#L208-L212)

### Dynamic Configuration

ViewSets support dynamic configuration based on request context through method overrides:

* `get_permissions()` - Dynamically determine permission classes
* `get_paginated_response()` - Customize pagination response format
* `paginate_queryset()` - Override pagination behavior

Sources: [fastapp/views/viewsets.py L208-L212](/fastapp/views/viewsets.py#L208-L212)

 [fastapp/views/viewsets.py L456-L475](/fastapp/views/viewsets.py#L456-L475)