# Database Migrations and Schema

> **Relevant source files**
> * [fastapp/commands/db.py](/fastapp/commands/db.py)
> * [fastapp/db/migrate.py](/fastapp/db/migrate.py)
> * [fastapp/tools/get_table_structure.py](/fastapp/tools/get_table_structure.py)

This document covers QingKongFramework's database migration system, schema generation utilities, and automatic migration capabilities. The system provides Django-like migration functionality built on top of Tortoise ORM, with support for PostgreSQL, MySQL, and SQLite databases.

For information about data loading and fixtures, see [Data Loading and Fixtures](Data-Loading-and-Fixtures.md). For database CLI commands, see [Database Commands](Database-Commands.md).

## Migration System Overview

QingKongFramework provides a comprehensive migration system that handles schema changes, automatic migration detection, and reverse engineering from existing databases. The system is built around three core components: the CLI interface, migration engine, and schema exporters.

**Migration Architecture**

```mermaid
flowchart TD

migrate["migrate"]
auto_migrate["auto_migrate"]
reverse_generation["reverse_generation"]
async_migrate["async_migrate"]
async_auto_migrate["async_auto_migrate"]
generate_schemas["generate_schemas"]
parse_sql["parse_sql"]
generate_diff_sql["generate_diff_sql"]
SchemaExporter["SchemaExporter"]
AsyncpgDumper["AsyncpgDumper"]
AsyncmyDumper["AsyncmyDumper"]
AiosqliteDumper["AiosqliteDumper"]
Tortoise["Tortoise ORM"]
sqlglot["sqlglot Parser"]
connections["DB Connections"]
table_to_django_model["table_to_django_model"]

migrate --> async_migrate
auto_migrate --> async_auto_migrate
reverse_generation --> table_to_django_model
async_auto_migrate --> SchemaExporter
async_auto_migrate --> parse_sql
async_auto_migrate --> generate_diff_sql
SchemaExporter --> AsyncpgDumper
SchemaExporter --> AsyncmyDumper
SchemaExporter --> AiosqliteDumper
parse_sql --> sqlglot
generate_schemas --> Tortoise
AsyncpgDumper --> connections
AsyncmyDumper --> connections
AiosqliteDumper --> connections

subgraph subGraph4 ["External Systems"]
    Tortoise
    sqlglot
    connections
end

subgraph subGraph3 ["Database Backends"]
    AsyncpgDumper
    AsyncmyDumper
    AiosqliteDumper
end

subgraph subGraph2 ["Schema Processing"]
    parse_sql
    generate_diff_sql
    SchemaExporter
end

subgraph subGraph1 ["Migration Engine"]
    async_migrate
    async_auto_migrate
    generate_schemas
    async_migrate --> generate_schemas
end

subgraph subGraph0 ["CLI Layer"]
    migrate
    auto_migrate
    reverse_generation
end
```

Sources: [fastapp/commands/db.py L37-L124](/fastapp/commands/db.py#L37-L124)

 [fastapp/db/migrate.py L369-L379](/fastapp/db/migrate.py#L369-L379)

 [fastapp/tools/get_table_structure.py L240-L263](/fastapp/tools/get_table_structure.py#L240-L263)

## Schema Generation and Management

The framework uses `generate_schemas` from `fastapp.db.utils` to create and modify database schemas based on Tortoise ORM models. This process integrates with the application discovery system and handles content types and permissions for built-in apps.

**Schema Generation Process**

```mermaid
sequenceDiagram
  participant migrate CLI
  participant async_migrate
  participant init_apps
  participant async_init_db
  participant generate_schemas
  participant ContentType Model
  participant Permission Model

  migrate CLI->>async_migrate: "safe, guided, apps, models"
  async_migrate->>init_apps: "settings.INSTALLED_APPS"
  async_migrate->>async_init_db: "get_tortoise_config()"
  async_migrate->>generate_schemas: "Tortoise, safe, guided, apps, models"
  loop ["Content Types Enabled"]
    async_migrate->>ContentType Model: "get_or_create for each model"
    async_migrate->>Permission Model: "create default permissions"
  end
  async_migrate->>async_migrate: "close connections"
```

The migration system validates app dependencies, ensuring that `fastapp.contrib.auth` requires `fastapp.contrib.contenttypes`, and `fastapp.contrib.guardian` requires `fastapp.contrib.auth`.

Sources: [fastapp/commands/db.py L46-L66](/fastapp/commands/db.py#L46-L66)

 [fastapp/commands/db.py L73-L123](/fastapp/commands/db.py#L73-L123)

## Auto-Migration with Diff Detection

The `auto_migrate` command provides automatic schema comparison and migration generation. It compares the current database schema with the expected schema from Tortoise models and generates SQL statements for any differences.

**Auto-Migration Workflow**

```mermaid
flowchart TD

generate_diff_sql["generate_diff_sql"]
detect_renames["Column Rename Detection"]
handle_drops["DROP COLUMN"]
handle_adds["ADD COLUMN"]
handle_modifies["MODIFY COLUMN"]
handle_indexes["Index Changes"]
parse_sql["parse_sql"]
sqlglot_parse["sqlglot.parse()"]
extract_tables["Extract Tables"]
extract_columns["Extract Columns"]
extract_indexes["Extract Indexes"]
A["async_auto_migrate"]
B["Get Tortoise Apps"]
C["For Each Model"]
D["SchemaExporter.export()"]
E["Generate Expected Schema"]
F["parse_sql(old_schema)"]
G["parse_sql(new_schema)"]
H["generate_diff_sql()"]
I["User Confirmation"]
J["Execute SQL"]

subgraph subGraph2 ["Diff Generation"]
    generate_diff_sql
    detect_renames
    handle_drops
    handle_adds
    handle_modifies
    handle_indexes
    generate_diff_sql --> detect_renames
    generate_diff_sql --> handle_drops
    generate_diff_sql --> handle_adds
    generate_diff_sql --> handle_modifies
    generate_diff_sql --> handle_indexes
end

subgraph subGraph1 ["SQL Parser Components"]
    parse_sql
    sqlglot_parse
    extract_tables
    extract_columns
    extract_indexes
    parse_sql --> sqlglot_parse
    sqlglot_parse --> extract_tables
    sqlglot_parse --> extract_columns
    sqlglot_parse --> extract_indexes
end

subgraph subGraph0 ["Schema Comparison Process"]
    A
    B
    C
    D
    E
    F
    G
    H
    I
    J
    A --> B
    B --> C
    C --> D
    C --> E
    D --> F
    E --> G
    F --> H
    G --> H
    H --> I
    I --> J
end
```

Sources: [fastapp/commands/db.py L188-L298](/fastapp/commands/db.py#L188-L298)

 [fastapp/db/migrate.py L349-L367](/fastapp/db/migrate.py#L349-L367)

## SQL Parsing and Schema Analysis

The migration system uses `sqlglot` to parse SQL statements and extract schema information. The `parse_sql` function handles CREATE TABLE and CREATE INDEX statements across different database dialects.

| SQL Element | Extraction Method | Supported Dialects |
| --- | --- | --- |
| Table Definition | `exp.Create` + `exp.Schema` | PostgreSQL, MySQL, SQLite |
| Column Definitions | `exp.ColumnDef` | All |
| Constraints | `exp.Constraint`, `exp.UniqueColumnConstraint` | All |
| Indexes | `exp.IndexColumnConstraint`, `exp.Create` + `exp.Index` | All |
| Data Types | `generator.datatype_sql()` | Dialect-specific |

**Column Change Detection Logic**

```mermaid
flowchart TD

NUMBER_TYPE_SET["NUMBER_TYPE_SET"]
skip_length["Skip Length Changes"]
TINYINT_BOOLEAN["TINYINT_BOOLEAN"]
skip_bool["Skip TINYINT(1) → BOOLEAN"]
BIGINT_BIGSERIAL["BIGINT_BIGSERIAL"]
skip_serial["Skip BIGINT(64) → BIGSERIAL"]
TEXT_JSON["TEXT_JSON"]
skip_json["Skip TEXT → JSON"]
old_cols["Old Columns"]
similarity["Calculate Similarity"]
new_cols["New Columns"]
renames["Possible Renames"]
user_confirm["User Confirmation"]
rename_ops["RENAME COLUMN"]
deleted["Deleted Columns"]
added["Added Columns"]
drop_ops["DROP COLUMN"]
add_ops["ADD COLUMN"]
common["Common Columns"]
type_compare["Type Comparison"]
modify_ops["MODIFY COLUMN"]

subgraph subGraph1 ["Type Compatibility"]
    NUMBER_TYPE_SET
    skip_length
    TINYINT_BOOLEAN
    skip_bool
    BIGINT_BIGSERIAL
    skip_serial
    TEXT_JSON
    skip_json
    NUMBER_TYPE_SET --> skip_length
    TINYINT_BOOLEAN --> skip_bool
    BIGINT_BIGSERIAL --> skip_serial
    TEXT_JSON --> skip_json
end

subgraph subGraph0 ["Column Comparison"]
    old_cols
    similarity
    new_cols
    renames
    user_confirm
    rename_ops
    deleted
    added
    drop_ops
    add_ops
    common
    type_compare
    modify_ops
    old_cols --> similarity
    new_cols --> similarity
    similarity --> renames
    renames --> user_confirm
    user_confirm --> rename_ops
    old_cols --> deleted
    new_cols --> added
    deleted --> drop_ops
    added --> add_ops
    common --> type_compare
    type_compare --> modify_ops
end
```

Sources: [fastapp/db/migrate.py L61-L210](/fastapp/db/migrate.py#L61-L210)

 [fastapp/db/migrate.py L213-L215](/fastapp/db/migrate.py#L213-L215)

 [fastapp/db/migrate.py L217-L346](/fastapp/db/migrate.py#L217-L346)

## Multi-Database Schema Export

The `SchemaExporter` class provides database-agnostic schema extraction using specialized dumper classes for each database backend. Each dumper handles the specific DDL syntax and metadata queries for its respective database.

**Database-Specific Schema Extraction**

| Database | Dumper Class | Key Features |
| --- | --- | --- |
| PostgreSQL | `AsyncpgDumper` | Full constraint support, vector column handling, pg_catalog queries |
| MySQL | `AsyncmyDumper` | SHOW CREATE TABLE, index filtering |
| SQLite | `AiosqliteDumper` | sqlite_master queries, index extraction |

**PostgreSQL Schema Extraction Process**

```mermaid
flowchart TD

get_ddl["get_ddl()"]
check_exists["_check_exists()"]
get_meta["_get_table_meta()"]
get_columns["_get_columns()"]
get_constraints["_get_constraints()"]
get_indexes["_get_indexes()"]
get_vector_info["_get_vector_column_info()"]
generate_table_ddl["_generate_table_ddl()"]
generate_index_ddl["_generate_index_ddl()"]
information_schema_columns["information_schema.columns"]
pg_constraint["pg_constraint, pg_class"]
pg_indexes["pg_indexes"]
pg_catalog["pg_catalog.pg_attribute"]

get_columns --> information_schema_columns
get_constraints --> pg_constraint
get_indexes --> pg_indexes
get_vector_info --> pg_catalog

subgraph subGraph1 ["Information Schema Queries"]
    information_schema_columns
    pg_constraint
    pg_indexes
    pg_catalog
end

subgraph subGraph0 ["AsyncpgDumper Methods"]
    get_ddl
    check_exists
    get_meta
    get_columns
    get_constraints
    get_indexes
    get_vector_info
    generate_table_ddl
    generate_index_ddl
    get_ddl --> check_exists
    check_exists --> get_meta
    get_meta --> get_columns
    get_meta --> get_constraints
    get_meta --> get_indexes
    get_meta --> get_vector_info
    get_meta --> generate_table_ddl
    get_meta --> generate_index_ddl
end
```

The PostgreSQL dumper includes special handling for vector columns (pgvector extension) and extracts dimension information from `pg_catalog` system tables.

Sources: [fastapp/tools/get_table_structure.py L18-L179](/fastapp/tools/get_table_structure.py#L18-L179)

 [fastapp/tools/get_table_structure.py L181-L213](/fastapp/tools/get_table_structure.py#L181-L213)

 [fastapp/tools/get_table_structure.py L215-L237](/fastapp/tools/get_table_structure.py#L215-L237)

## Reverse Engineering and Model Generation

The `reverse_generation` command allows developers to generate Django/Tortoise model definitions from existing database tables. This is particularly useful when working with legacy databases or when starting a new project with an existing schema.

**Reverse Generation Command Structure**

```mermaid
flowchart TD

table_arg["table (required)"]
connection_opt["--connection (default)"]
db_opt["--db (optional)"]
reverse_generation["reverse_generation"]
get_db_config["settings.DATABASES[connection]"]
build_config["Build Connection Config"]
table_to_django_model["table_to_django_model()"]
print_result["Print Generated Model"]
HOST["HOST"]
PORT["PORT"]
USER["USER"]
PASSWORD["PASSWORD"]
NAME["DB NAME"]

get_db_config --> HOST
get_db_config --> PORT
get_db_config --> USER
get_db_config --> PASSWORD
get_db_config --> NAME

subgraph subGraph2 ["Database Config"]
    HOST
    PORT
    USER
    PASSWORD
    NAME
end

subgraph subGraph1 ["Process Flow"]
    reverse_generation
    get_db_config
    build_config
    table_to_django_model
    print_result
    reverse_generation --> get_db_config
    get_db_config --> build_config
    build_config --> table_to_django_model
    table_to_django_model --> print_result
end

subgraph subGraph0 ["CLI Parameters"]
    table_arg
    connection_opt
    db_opt
end
```

Sources: [fastapp/commands/db.py L159-L185](/fastapp/commands/db.py#L159-L185)

 [fastapp/commands/db.py L147-L156](/fastapp/commands/db.py#L147-L156)

## Migration Safety and Validation

The migration system includes several safety mechanisms to prevent data loss and ensure migration integrity:

### Safety Features

* **Guided Mode**: Interactive confirmation for each SQL statement during auto-migration
* **Safe Mode**: Default enabled for all migration operations
* **Dependency Validation**: Ensures required apps are installed before migration
* **Connection Management**: Proper cleanup of database connections after operations
* **PostgreSQL Sequence Reset**: Automatic sequence adjustment for auto-increment fields

### App Dependency Checks

```markdown
# From fastapp/commands/db.py:46-62
INTERNAL_CONTENTTYPES_APP_LABEL = "fastapp.contrib.contenttypes"
INTERNAL_AUTH_APP_LABEL = "fastapp.contrib.auth" 
INTERNAL_GUARDIAN_APP_LABEL = "fastapp.contrib.guardian"

# Auth app requires contenttypes
if auth_app_enabled and not content_type_app_enabled:
    click.echo("ERROR fastapp.contrib.auth required fastapp.contrib.contenttypes")
    
# Guardian app requires auth
if guardian_app_enabled and not auth_app_enabled:
    click.echo("ERROR fastapp.contrib.guardian required fastapp.contrib.auth")
```

Sources: [fastapp/commands/db.py L32-L62](/fastapp/commands/db.py#L32-L62)

 [fastapp/commands/db.py L115-L123](/fastapp/commands/db.py#L115-L123)

 [fastapp/commands/db.py L254-L284](/fastapp/commands/db.py#L254-L284)