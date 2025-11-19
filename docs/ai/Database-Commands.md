# Database Commands

> **Relevant source files**
> * [fastapp/commands/db.py](/fastapp/commands/db.py)
> * [fastapp/db/migrate.py](/fastapp/db/migrate.py)
> * [fastapp/tools/get_table_structure.py](/fastapp/tools/get_table_structure.py)

This document covers the command-line interface tools for database operations in QingKongFramework. These CLI commands provide database migration, schema generation, and reverse engineering capabilities through the `manage.py` interface.

For information about the underlying database migration system and schema management implementation, see [Database Migrations and Schema](Database-Migrations-and-Schema.md).

## Overview

The database commands module provides three primary CLI tools for database management:

* **migrate** - Execute database migrations with support for safe and guided operations
* **auto_migrate** - Automatically detect schema changes and generate migration scripts
* **reverse_generation** - Generate Django model definitions from existing database tables

These commands integrate with QingKongFramework's application system and support PostgreSQL, MySQL, and SQLite databases through the Tortoise ORM backend.

## Command Architecture

```mermaid
flowchart TD

MigrateCmd["migrate()"]
AutoMigrateCmd["auto_migrate()"]
ReverseGenCmd["reverse_generation()"]
AsyncMigrate["async_migrate()"]
AsyncAutoMigrate["async_auto_migrate()"]
TableToDjango["table_to_django_model()"]
GenerateSchemas["generate_schemas()"]
ParseSQL["parse_sql()"]
GenerateDiffSQL["generate_diff_sql()"]
GenerateAlter["generate_alter_statements()"]
SchemaExporter["SchemaExporter"]
AsyncpgDumper["AsyncpgDumper"]
AsyncmyDumper["AsyncmyDumper"]
AiosqliteDumper["AiosqliteDumper"]
TortoiseORM["Tortoise ORM"]
Connections["connections[]"]

MigrateCmd --> AsyncMigrate
AutoMigrateCmd --> AsyncAutoMigrate
ReverseGenCmd --> TableToDjango
AsyncMigrate --> GenerateSchemas
AsyncAutoMigrate --> SchemaExporter
AsyncAutoMigrate --> ParseSQL
AsyncAutoMigrate --> GenerateDiffSQL
AsyncMigrate --> TortoiseORM
AsyncAutoMigrate --> Connections
SchemaExporter --> Connections

subgraph subGraph4 ["Database Connections"]
    TortoiseORM
    Connections
end

subgraph subGraph3 ["Schema Export System"]
    SchemaExporter
    AsyncpgDumper
    AsyncmyDumper
    AiosqliteDumper
    SchemaExporter --> AsyncpgDumper
    SchemaExporter --> AsyncmyDumper
    SchemaExporter --> AiosqliteDumper
end

subgraph subGraph2 ["Core Migration Engine"]
    GenerateSchemas
    ParseSQL
    GenerateDiffSQL
    GenerateAlter
    GenerateDiffSQL --> GenerateAlter
end

subgraph subGraph1 ["Async Implementation Layer"]
    AsyncMigrate
    AsyncAutoMigrate
    TableToDjango
end

subgraph subGraph0 ["CLI Entry Points"]
    MigrateCmd
    AutoMigrateCmd
    ReverseGenCmd
end
```

**Sources:** [fastapp/commands/db.py L1-L299](/fastapp/commands/db.py#L1-L299)

 [fastapp/db/migrate.py L1-L379](/fastapp/db/migrate.py#L1-L379)

 [fastapp/tools/get_table_structure.py L1-L295](/fastapp/tools/get_table_structure.py#L1-L295)

## Migration Commands

### migrate Command

The `migrate` command executes database schema migrations with support for application-specific and model-specific targeting.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `--safe` | boolean | `True` | Enable safe migration mode |
| `--guided` | boolean | `True` | Enable interactive guided migration |
| `--apps` | multiple | `[]` | Target specific applications |
| `--models` | multiple | `[]` | Target specific models |

```markdown
# Basic migration
python manage.py migrate

# Migration with specific options
python manage.py migrate --safe=False --guided=False

# Target specific apps and models
python manage.py migrate --apps myapp --models MyModel
```

#### Migration Process Flow

```mermaid
sequenceDiagram
  participant migrate CLI
  participant async_migrate()
  participant init_apps()
  participant async_init_db()
  participant generate_schemas()
  participant ContentType Model
  participant Permission Model

  migrate CLI->>async_migrate(): "safe, guided, apps, models"
  async_migrate()->>async_migrate(): "Validate app dependencies"
  async_migrate()->>init_apps(): "settings.INSTALLED_APPS"
  async_migrate()->>async_init_db(): "get_tortoise_config()"
  async_migrate()->>generate_schemas(): "Tortoise, safe, guided, apps, models"
  loop ["Content types enabled"]
    async_migrate()->>ContentType Model: "get_or_create() for each model"
    async_migrate()->>Permission Model: "create default permissions"
  end
  async_migrate()->>async_migrate(): "Close database connections"
```

**Sources:** [fastapp/commands/db.py L37-L124](/fastapp/commands/db.py#L37-L124)

 [fastapp/commands/db.py L126-L144](/fastapp/commands/db.py#L126-L144)

### auto_migrate Command

The `auto_migrate` command automatically detects schema differences and generates migration SQL by comparing current database structure with model definitions.

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `--apps` | multiple | `[]` | Target specific applications |
| `--guided` | boolean | `True` | Enable interactive SQL execution |

```markdown
# Auto-migrate all apps
python manage.py auto_migrate

# Auto-migrate specific apps
python manage.py auto_migrate --apps myapp --apps anotherapp

# Non-interactive mode
python manage.py auto_migrate --guided=False
```

#### Auto-Migration Algorithm

```mermaid
flowchart TD

StartApps["Iterate Tortoise.apps"]
CheckManaged["Check model._meta.is_managed"]
ExportCurrent["SchemaExporter.export()"]
GenerateNew["conn.schema_generator()._get_table_sql()"]
ParseSchemas["parse_sql() old vs new"]
DetectChanges["generate_diff_sql()"]
ColumnChanges["Column additions/deletions"]
TypeChanges["Data type modifications"]
IndexChanges["Index additions/deletions"]
ConstraintChanges["Constraint modifications"]
DisplaySQL["Display generated SQL"]
UserPrompt["Prompt: Y/N/Q"]
ExecuteSQL["Execute SQL statements"]

DetectChanges --> ColumnChanges
DetectChanges --> TypeChanges
DetectChanges --> IndexChanges
DetectChanges --> ConstraintChanges
DetectChanges --> DisplaySQL

subgraph subGraph2 ["User Interaction"]
    DisplaySQL
    UserPrompt
    ExecuteSQL
    DisplaySQL --> UserPrompt
    UserPrompt --> ExecuteSQL
end

subgraph subGraph1 ["Change Detection"]
    ColumnChanges
    TypeChanges
    IndexChanges
    ConstraintChanges
end

subgraph subGraph0 ["Schema Comparison Process"]
    StartApps
    CheckManaged
    ExportCurrent
    GenerateNew
    ParseSchemas
    DetectChanges
    StartApps --> CheckManaged
    CheckManaged --> ExportCurrent
    ExportCurrent --> GenerateNew
    GenerateNew --> ParseSchemas
    ParseSchemas --> DetectChanges
end
```

**Sources:** [fastapp/commands/db.py L188-L285](/fastapp/commands/db.py#L188-L285)

 [fastapp/commands/db.py L287-L298](/fastapp/commands/db.py#L287-L298)

## Schema Generation and Reverse Engineering

### reverse_generation Command

The `reverse_generation` command generates Django model definitions from existing database tables.

| Argument | Type | Description |
| --- | --- | --- |
| `table` | string | Target table name |

| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `--connection` | string | `"default"` | Database connection name |
| `--db` | string | `None` | Override database name |

```python
# Generate model from table
python manage.py reverse_generation users

# Use specific connection and database
python manage.py reverse_generation products --connection=secondary --db=inventory
```

#### Table Structure Export System

```mermaid
flowchart TD

SchemaExporter["SchemaExporter(conn_name, tables)"]
GetDumperClass["_get_dumper_class()"]
AsyncpgDumper["AsyncpgDumper<br>PostgreSQL"]
AsyncmyDumper["AsyncmyDumper<br>MySQL"]
AiosqliteDumper["AiosqliteDumper<br>SQLite"]
GetColumns["_get_columns()"]
GetConstraints["_get_constraints()"]
GetIndexes["_get_indexes()"]
GetComments["_get_table_comment()"]
GetVectorInfo["_get_vector_column_info()"]
GenerateTableDDL["_generate_table_ddl()"]
GenerateIndexDDL["_generate_index_ddl()"]
GetColumnType["_get_column_type()"]

GetDumperClass --> AsyncpgDumper
GetDumperClass --> AsyncmyDumper
GetDumperClass --> AiosqliteDumper
AsyncpgDumper --> GetColumns
AsyncpgDumper --> GetConstraints
AsyncpgDumper --> GetIndexes
AsyncpgDumper --> GetComments
AsyncpgDumper --> GetVectorInfo
GetColumns --> GenerateTableDDL
GetConstraints --> GenerateTableDDL
GetComments --> GenerateTableDDL
GetVectorInfo --> GetColumnType
GetIndexes --> GenerateIndexDDL

subgraph subGraph3 ["DDL Generation"]
    GenerateTableDDL
    GenerateIndexDDL
    GetColumnType
end

subgraph subGraph2 ["Metadata Extraction"]
    GetColumns
    GetConstraints
    GetIndexes
    GetComments
    GetVectorInfo
end

subgraph subGraph1 ["Database-Specific Dumpers"]
    AsyncpgDumper
    AsyncmyDumper
    AiosqliteDumper
end

subgraph subGraph0 ["SchemaExporter Factory"]
    SchemaExporter
    GetDumperClass
    SchemaExporter --> GetDumperClass
end
```

**Sources:** [fastapp/commands/db.py L159-L185](/fastapp/commands/db.py#L159-L185)

 [fastapp/tools/get_table_structure.py L240-L274](/fastapp/tools/get_table_structure.py#L240-L274)

## Schema Parsing and Diff Generation

### SQL Schema Parsing

The migration system uses `sqlglot` for parsing SQL schemas and detecting differences between database states.

#### Schema Parsing Process

| Component | Purpose | Key Operations |
| --- | --- | --- |
| `parse_sql()` | Parse SQL DDL statements | Extract tables, columns, indexes, constraints |
| `generate_diff_sql()` | Compare schema versions | Detect additions, deletions, modifications |
| `generate_alter_statements()` | Create migration SQL | Generate ALTER TABLE statements |

#### Column Change Detection

```mermaid
flowchart TD

OldSchema["Old Schema<br>parse_sql(old_ddl)"]
NewSchema["New Schema<br>parse_sql(new_ddl)"]
CompareColumns["Compare Columns<br>calculate_similarity()"]
DetectRenames["Detect Renames<br>similarity > 0.6"]
GenerateAlters["Generate ALTER Statements"]
AddColumns["ADD COLUMN"]
DropColumns["DROP COLUMN"]
RenameColumns["RENAME COLUMN"]
ModifyColumns["MODIFY COLUMN"]
AddIndexes["CREATE INDEX"]
DropIndexes["DROP INDEX"]

GenerateAlters --> AddColumns
GenerateAlters --> DropColumns
GenerateAlters --> RenameColumns
GenerateAlters --> ModifyColumns
GenerateAlters --> AddIndexes
GenerateAlters --> DropIndexes

subgraph subGraph1 ["Supported Changes"]
    AddColumns
    DropColumns
    RenameColumns
    ModifyColumns
    AddIndexes
    DropIndexes
end

subgraph subGraph0 ["Change Detection Algorithm"]
    OldSchema
    NewSchema
    CompareColumns
    DetectRenames
    GenerateAlters
    OldSchema --> CompareColumns
    NewSchema --> CompareColumns
    CompareColumns --> DetectRenames
    DetectRenames --> GenerateAlters
end
```

**Sources:** [fastapp/db/migrate.py L61-L210](/fastapp/db/migrate.py#L61-L210)

 [fastapp/db/migrate.py L217-L346](/fastapp/db/migrate.py#L217-L346)

 [fastapp/db/migrate.py L349-L366](/fastapp/db/migrate.py#L349-L366)

## Database Support Matrix

| Feature | PostgreSQL | MySQL | SQLite |
| --- | --- | --- | --- |
| Schema Export | ✓ | ✓ | ✓ |
| Migration Detection | ✓ | ✓ | ✓ |
| Reverse Generation | ✓ | ✓ | ✓ |
| Vector Columns | ✓ | ✗ | ✗ |
| Expression Indexes | ✓ | Limited | ✗ |
| Column Rename Detection | ✓ | ✓ | ✓ |

### Database-Specific Implementation

The framework automatically detects the database backend and uses appropriate SQL dialects and schema export mechanisms:

* **PostgreSQL**: Uses `information_schema` queries for metadata extraction
* **MySQL**: Uses `SHOW CREATE TABLE` and `SHOW INDEX` statements
* **SQLite**: Uses `sqlite_master` table queries

**Sources:** [fastapp/tools/get_table_structure.py L18-L179](/fastapp/tools/get_table_structure.py#L18-L179)

 [fastapp/tools/get_table_structure.py L181-L213](/fastapp/tools/get_table_structure.py#L181-L213)

 [fastapp/tools/get_table_structure.py L215-L238](/fastapp/tools/get_table_structure.py#L215-L238)