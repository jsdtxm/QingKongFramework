# BaseModel Extensions

> **Relevant source files**
> * [fastapp/db/backends/mixin.py](/fastapp/db/backends/mixin.py)
> * [fastapp/db/utils.py](/fastapp/db/utils.py)
> * [fastapp/models/base.py](/fastapp/models/base.py)
> * [fastapp/models/info.py](/fastapp/models/info.py)
> * [fastapp/models/manager.py](/fastapp/models/manager.py)
> * [fastapp/models/queryset.py](/fastapp/models/queryset.py)

The BaseModel Extensions system provides enhanced database model functionality built on top of Tortoise ORM. This system includes custom QuerySet implementations, Manager classes, schema generation utilities, and TimescaleDB integration. It serves as the foundation for the data layer in QingKongFramework, providing Django-like ORM patterns with async capabilities.

For dynamic query filtering with Pydantic validation, see [FilterSet System](FilterSet-System.md). For Tortoise ORM to Pydantic model conversion, see [ModelSerializer System](ModelSerializer-System.md). For custom database functions and indexing, see [Database Functions and Indexing](Database-Functions-and-Indexing.md).

## BaseModel Architecture

The `BaseModel` class extends Tortoise ORM's `Model` with enhanced metadata handling, custom QuerySet/Manager integration, and automatic application configuration.

### BaseModel Class Hierarchy

```mermaid
classDiagram
    class TortoiseModel {
        +Meta: ModelMeta
        +filter(**kwargs) : QuerySet
        +create(**kwargs) : Model
    }
    class ModelMetaClass {
        +new() : type
        +_configure_app_metadata()
        +_configure_table_name()
    }
    class BaseModel {
        +app: AppConfig
        +objects: Manager
        +Meta: BaseMeta
        +PydanticMeta: class
        +StubGenMeta: class
        +filter() : QuerySet
        +generate_query_params() : tuple
    }
    class BaseMeta {
        +external: bool
        +managed: bool
        +ignore_schema: Optional[bool]
        +app: str
        +permissions: List
    }
    class MetaInfo {
        +external: bool
        +managed: bool
        +ignore_schema: bool
        +app_config: AppConfig
        +manager: Manager
        +is_managed: bool
        +data_fields() : list
    }
    TortoiseModel <|-- BaseModel : metaclass
    BaseModel <|-- ModelMetaClass : Meta
    BaseModel <-- BaseMeta : _meta
    BaseModel <-- MetaInfo
```

Sources: [fastapp/models/base.py L20-L297](/fastapp/models/base.py#L20-L297)

 [fastapp/models/info.py L12-L39](/fastapp/models/info.py#L12-L39)

### BaseModel Metaclass Processing

```mermaid
flowchart TD

Start["ModelMetaClass.new()"]
CheckModule["module.endswith('.models')?"]
GetMeta["Get Meta class or create BaseMeta"]
CallSuper["Call super().new()"]
CheckAbstract["abstract=True?"]
ConfigureApp["Configure app metadata"]
SetMeta["Set Meta attributes"]
SetAppConfig["attrs['app'] = app_config<br>meta_class.app = app_config.label"]
SetVerboseName["Set verbose_name if None"]
ConfigureTable["Configure table name"]
CheckTable["table or db_table exists?"]
GenerateTable["table = f'{app_label}_{model_name}'"]
UseExisting["Use existing table name"]
End["Return new class"]

Start --> CheckModule
CheckModule --> GetMeta
CheckModule --> CallSuper
GetMeta --> CheckAbstract
CheckAbstract --> ConfigureApp
CheckAbstract --> SetMeta
ConfigureApp --> SetAppConfig
SetAppConfig --> SetVerboseName
SetVerboseName --> ConfigureTable
ConfigureTable --> CheckTable
CheckTable --> GenerateTable
CheckTable --> UseExisting
GenerateTable --> SetMeta
UseExisting --> SetMeta
SetMeta --> CallSuper
CallSuper --> End
```

Sources: [fastapp/models/base.py L29-L66](/fastapp/models/base.py#L29-L66)

## QuerySet Enhancements

The custom `QuerySet` class extends Tortoise ORM's QuerySet with additional functionality including deferred field loading, named tuple results, and enhanced select_related support.

### QuerySet Feature Overview

| Feature | Method | Description |
| --- | --- | --- |
| Deferred Fields | `defer(*fields)` | Exclude specified fields from SELECT |
| Named Tuples | `values_list(named=True)` | Return named tuples instead of regular tuples |
| Database Selection | `using(db_name)` | Use specific database connection |
| Enhanced Join | `_join_table_with_select_related()` | Support deferred fields in joins |

### QuerySet Method Flow

```mermaid
flowchart TD

QuerySetInit["QuerySet.init()"]
SetDefaults["self._fields_for_exclude = ()"]
DeferCall["defer(*fields)"]
CloneQS["queryset = self._clone()"]
SetExclude["queryset._fields_for_exclude = fields"]
ValuesListCall["values_list(*fields, named=True)"]
CreateVLQ["ValuesListQuery(named=True)"]
ExecuteQuery["await()"]
CheckNamed["named=True?"]
NamedTuples["values_list_to_named()"]
RegularTuples["Regular tuple results"]
SimpleNamespace["SimpleNamespace(**dict(zip(...)))"]
JoinTable["_join_table_with_select_related()"]
CheckDefer["field in _fields_for_exclude?"]
SkipField["Skip field in SELECT"]
AddField["Add field to SELECT"]

QuerySetInit --> SetDefaults
DeferCall --> CloneQS
CloneQS --> SetExclude
ValuesListCall --> CreateVLQ
CreateVLQ --> ExecuteQuery
ExecuteQuery --> CheckNamed
CheckNamed --> NamedTuples
CheckNamed --> RegularTuples
NamedTuples --> SimpleNamespace
JoinTable --> CheckDefer
CheckDefer --> SkipField
CheckDefer --> AddField
```

Sources: [fastapp/models/queryset.py L88-L224](/fastapp/models/queryset.py#L88-L224)

## Manager System

The `Manager` class provides the query interface for models, extending Tortoise ORM's Manager with enhanced QuerySet integration and factory methods.

### Manager Class Structure

```mermaid
classDiagram
    class TortoiseManager {
        +get_queryset() : QuerySet
    }
    class Manager {
        +_model: BaseModel
        +_queryset_class: Type[QuerySet]
        +from_queryset() : Manager
        +create(**kwargs) : MODEL
        +get_or_create(**kwargs) : tuple
        +get_queryset() : QuerySet[MODEL]
        +getattr(item) : Any
    }
    class QuerySet {
        +filter() : Self
        +all() : Self
        +create() : MODEL
        +using() : Self
        +defer() : Self
    }
    class BaseModel {
    }
    TortoiseManager <|-- Manager : uses
    Manager --> QuerySet : manages
    Manager --> BaseModel
```

Sources: [fastapp/models/manager.py L19-L59](/fastapp/models/manager.py#L19-L59)

## Schema Generation and Database Utilities

The schema generation system provides enhanced database schema creation with application filtering, TimescaleDB support, and guided migration capabilities.

### Schema Generation Process

```mermaid
flowchart TD

StartSchema["generate_schemas()"]
CheckInit["Tortoise._inited?"]
ConfigError["Raise ConfigurationError"]
IterateConnections["For each connection"]
GetClient["client: BaseDBAsyncClient"]
GenerateForClient["generate_schema_for_client()"]
GetSchemaSQL["get_schema_sql()"]
GetModelsToCreate["_get_models_to_create()"]
FilterByApp["app.label in apps_list?"]
CheckManaged["model._meta.is_managed?"]
SkipModel["Skip model"]
AddToCreate["Add to tables_to_create"]
CheckHypertable["hasattr(Meta, 'hypertable')?"]
GenerateHypertable["generate_hypertable_sql()"]
StandardTable["Standard table creation"]
AddExtraSQL["Add to extra_sql"]
ExecuteSQL["Execute schema SQL"]

StartSchema --> CheckInit
CheckInit --> ConfigError
CheckInit --> IterateConnections
IterateConnections --> GetClient
GetClient --> GenerateForClient
GenerateForClient --> GetSchemaSQL
GetSchemaSQL --> GetModelsToCreate
GetModelsToCreate --> FilterByApp
FilterByApp --> CheckManaged
FilterByApp --> SkipModel
CheckManaged --> AddToCreate
CheckManaged --> SkipModel
AddToCreate --> CheckHypertable
CheckHypertable --> GenerateHypertable
CheckHypertable --> StandardTable
GenerateHypertable --> AddExtraSQL
AddExtraSQL --> StandardTable
StandardTable --> ExecuteSQL
```

Sources: [fastapp/db/utils.py L241-L272](/fastapp/db/utils.py#L241-L272)

 [fastapp/db/utils.py L108-L177](/fastapp/db/utils.py#L108-L177)

## TimescaleDB Integration

The system provides native support for TimescaleDB hypertables through the `hypertable` Meta attribute and automatic SQL generation.

### Hypertable Configuration

```mermaid
flowchart TD

ModelMeta["class Meta:<br>hypertable = {...}"]
ValidateConfig["Validate configuration"]
CheckTimeColumn["time_column_name exists?"]
RaiseError["ValueError: time_column_name required"]
CheckPartitioning["partitioning_column and<br>number_partitions both set?"]
RaiseError2["ValueError: Both or neither required"]
BuildParams["Build SQL parameters"]
AddTimeCol["params = [table_name, time_column]"]
AddPartitioning["Add partitioning params?"]
AddPartParams["Add partitioning_column,<br>number_partitions"]
AddInterval["Add chunk_time_interval"]
GenerateSQL["Generate DO $$ block:<br>- Drop existing PK<br>- Create hypertable"]
AddCompression["compress_segmentby exists?"]
AddCompressSQL["ALTER TABLE SET compress"]
AddPolicy["compression_policy exists?"]
AddPolicySQL["add_compression_policy()"]
ReturnSQL["Return complete SQL"]

ModelMeta --> ValidateConfig
ValidateConfig --> CheckTimeColumn
CheckTimeColumn --> RaiseError
CheckTimeColumn --> CheckPartitioning
CheckPartitioning --> RaiseError2
CheckPartitioning --> BuildParams
BuildParams --> AddTimeCol
AddTimeCol --> AddPartitioning
AddPartitioning --> AddPartParams
AddPartitioning --> AddInterval
AddPartParams --> AddInterval
AddInterval --> GenerateSQL
GenerateSQL --> AddCompression
AddCompression --> AddCompressSQL
AddCompression --> AddPolicy
AddCompressSQL --> AddPolicy
AddPolicy --> AddPolicySQL
AddPolicy --> ReturnSQL
AddPolicySQL --> ReturnSQL
```

Sources: [fastapp/db/utils.py L34-L106](/fastapp/db/utils.py#L34-L106)

### Hypertable SQL Generation Example

The `generate_hypertable_sql()` function creates complex PostgreSQL/TimescaleDB SQL:

| Configuration Key | Purpose | Required |
| --- | --- | --- |
| `time_column_name` | Primary time dimension | Yes |
| `partitioning_column` | Space partitioning field | No |
| `number_partitions` | Number of space partitions | No |
| `chunk_time_interval` | Time chunk size | No (default: '7 days') |
| `compress_segmentby` | Compression segment field | No |
| `compression_policy` | Auto-compression policy | No |

Sources: [fastapp/db/utils.py L34-L106](/fastapp/db/utils.py#L34-L106)

## Type Generation and Stub Support

The BaseModel system includes automatic type hint generation for query parameters and model creation parameters through the `generate_query_params()` method and `StubGenMeta` configuration.

### Query Parameter Generation

```mermaid
flowchart TD

GenerateParams["generate_query_params(mode)"]
GetFields["get model fields from describe()"]
FilterFields["field_filter(StubGenMeta, fields)"]
ProcessField["For each field"]
CheckFieldType["Field type?"]
ProcessRelational["Process FK/M2M/O2O"]
ProcessData["Process data field"]
CheckDepth["depth < max_depth?"]
RecursiveCall["Recursive generate_query_params()"]
SkipRelational["Skip relational field"]
AddRelationalParams["Add field and field__ params"]
CheckMode["mode='full' or field in full?"]
AddFullParams["Add __exact, __iexact, __isnull"]
AddBasicParams["Add basic params"]
CheckDataType["Data type?"]
AddRangeParams["Add __gt, __gte, __lt, __lte"]
AddStringParams["Add __contains, __icontains, etc"]
AddDateParams["Add __year, __month, __day, etc"]
GenerateTypedDict["Generate TypedDict classes"]
ReturnCode["Return CreateParams and QueryParams"]

GenerateParams --> GetFields
GetFields --> FilterFields
FilterFields --> ProcessField
ProcessField --> CheckFieldType
CheckFieldType --> ProcessRelational
CheckFieldType --> ProcessData
ProcessRelational --> CheckDepth
CheckDepth --> RecursiveCall
CheckDepth --> SkipRelational
RecursiveCall --> AddRelationalParams
ProcessData --> CheckMode
CheckMode --> AddFullParams
CheckMode --> AddBasicParams
AddFullParams --> CheckDataType
AddBasicParams --> CheckDataType
CheckDataType --> AddRangeParams
CheckDataType --> AddStringParams
CheckDataType --> AddDateParams
AddRangeParams --> GenerateTypedDict
AddStringParams --> GenerateTypedDict
AddDateParams --> GenerateTypedDict
GenerateTypedDict --> ReturnCode
```

Sources: [fastapp/models/base.py L96-L243](/fastapp/models/base.py#L96-L243)

 [fastapp/models/base.py L272-L294](/fastapp/models/base.py#L272-L294)

### StubGenMeta Configuration

The `StubGenMeta` class controls which fields are included in generated type stubs:

| Attribute | Type | Purpose |
| --- | --- | --- |
| `include` | `str` or `tuple` | Fields to include (`"__all__"` or specific fields) |
| `exclude` | `tuple` | Fields to exclude from generation |
| `full` | `tuple` | Fields to generate full query params for |

Sources: [fastapp/models/base.py L303-L307](/fastapp/models/base.py#L303-L307)