---
name: data-model-analysis
argument-hint: "[path to codebase root]"
description: >
  Analyzes the data model of a Java Spring Boot application including JPA/Hibernate entities,
  database schema, relationships, migrations, and query patterns. Produces ASCII ER diagrams,
  entity card visuals, relationship maps, migration timelines, and data flow diagrams. Use when
  onboarding to a codebase and needing to understand the database structure, entity relationships,
  or data flow through the system.
compatibility: Requires filesystem access to a Java Spring Boot + React codebase with source code
license: MIT
metadata:
  author: knowledge-transition
  version: "2.0"
  stack: java-springboot-react
---

# Data Model Analysis

## Automated Scanner

Before manual analysis, run the automated entity scanner to gather baseline metrics:

```bash
python scripts/scan_entities.py /path/to/codebase
```

This produces a JSON summary with entity counts, fields, relationships, cascade/fetch risks, repository query patterns, and migration counts. Use this data to populate the diagrams below.

## Purpose

Produce a complete, navigable map of the data model. Output is **primarily ASCII diagrams** — entity cards, ER relationship maps, migration timelines, cascade heatmaps, and data flow visuals — so new developers understand what data exists and how it flows, and QA can design data-driven test scenarios at a glance.

## When to use this skill

- New developer needs to understand the database structure
- QA needs to design test data strategies
- Reviewing a codebase with complex entity relationships
- No existing ER diagram or data dictionary
- Before making schema changes to understand impact

**Related skills**: `api-contract-discovery` (how entities surface in APIs), `dependency-flow-visualizer` (data flow tracing)

## Step 1: Identify the persistence strategy

Determine how the application manages data and produce a visual:

```
+===================================================================+
|                  PERSISTENCE STRATEGY OVERVIEW                    |
+===================================================================+
|                                                                   |
|  +------------------+     +------------------+                    |
|  | ORM / Data Layer |     | Database         |                    |
|  |------------------|     |------------------|                    |
|  | [ ] JPA+Hibernate|     | [ ] PostgreSQL   |                    |
|  | [ ] Spring JDBC  |     | [ ] MySQL        |                    |
|  | [ ] MyBatis      |     | [ ] Oracle       |                    |
|  | [ ] MongoDB      |     | [ ] MongoDB      |                    |
|  +------------------+     +------------------+                    |
|                                                                   |
|  +------------------+     +------------------+                    |
|  | Connection Pool  |     | Migration Tool   |                    |
|  |------------------|     |------------------|                    |
|  | [ ] HikariCP     |     | [ ] Flyway       |                    |
|  | [ ] Tomcat JDBC  |     | [ ] Liquibase    |                    |
|  | [ ] C3P0         |     | [ ] None/ddl-auto|                    |
|  +------------------+     +------------------+                    |
|                                                                   |
|  Schema Generation: spring.jpa.hibernate.ddl-auto = ________     |
|  Datasource URL: ____________________________________________    |
|                                                                   |
+===================================================================+
```

Where to look: `pom.xml` / `build.gradle` for dependencies, `application.yml` for config.

## Step 2: Catalog all entities — Entity Card Visuals

For each `@Entity` (or `@Document` for MongoDB), produce an **ASCII Entity Card**:

```
+============= USER ==============+     +============ ORDER =============+
| PK  id          BIGINT  NOT NULL|     | PK  id          BIGINT NOT NULL|
| UK  email       VARCHAR NOT NULL|     | FK  user_id     BIGINT NOT NULL|
|     name        VARCHAR         |     |     status      ENUM   NOT NULL|
|     status      ENUM           |     |     total       DECIMAL        |
|     password    VARCHAR NOT NULL|     | AUD created_at  TIMESTAMP      |
| AUD created_at  TIMESTAMP      |     | AUD updated_at  TIMESTAMP      |
| AUD updated_at  TIMESTAMP      |     +================================+
| VER version     INTEGER        |
+=================================+     +========== ORDER_ITEM ==========+
                                        | PK  id          BIGINT NOT NULL|
+============= ROLE ==============+     | FK  order_id    BIGINT NOT NULL|
| PK  id          BIGINT NOT NULL|     | FK  product_id  BIGINT NOT NULL|
|     name        VARCHAR UK     |     |     quantity    INTEGER NOT NULL|
|     description VARCHAR        |     |     unit_price  DECIMAL NOT NULL|
+=================================+     +================================+

+=========== PRODUCT =============+     +========== CATEGORY ============+
| PK  id          BIGINT NOT NULL|     | PK  id          BIGINT NOT NULL|
| FK  category_id BIGINT         |     |     name        VARCHAR UK     |
|     name        VARCHAR NOT NULL|     |     description VARCHAR        |
|     price       DECIMAL NOT NULL|     |     parent_id   BIGINT (self)  |
|     sku         VARCHAR UK     |     +================================+
| AUD created_at  TIMESTAMP      |
+=================================+

LEGEND:  PK = Primary Key    FK = Foreign Key    UK = Unique
         AUD = Audit field   VER = @Version (optimistic lock)
```

### Key annotations to extract

| Annotation                  | Information                                    |
|-----------------------------|------------------------------------------------|
| `@Table(name=)`             | Physical table name                            |
| `@Column`                   | Column name, nullable, unique, length          |
| `@Id`, `@GeneratedValue`   | Primary key strategy                           |
| `@Enumerated`               | Enum storage (STRING vs ORDINAL)               |
| `@CreatedDate`, `@LastModifiedDate` | Audit timestamps                      |
| `@Version`                  | Optimistic locking                             |
| `@Embedded`, `@Embeddable`  | Value objects                                  |

## Step 3: Map relationships — ASCII ER Diagram

Produce the **ASCII Entity-Relationship Diagram**:

```
+=====================================================================+
|                   ENTITY-RELATIONSHIP DIAGRAM                       |
+=====================================================================+
|                                                                     |
|  +--------+   1    *   +--------+   1    *   +-----------+          |
|  |  USER  |----------->| ORDER  |----------->| ORDER_ITEM|          |
|  |        |  places    |        |  contains  |           |          |
|  +---+----+            +---+----+            +-----+-----+          |
|      |                     |                       |                |
|      | *                   | 1                     | *              |
|      |                     |                       |                |
|      |  +--------+         |                  +----+-----+          |
|      +->|  ROLE  |         |                  | PRODUCT  |          |
|     has  |        |         +---------------->|          |          |
|     *..* +--------+           generates 1..1  +----+-----+          |
|                                                    |                |
|          +----------+                              | *              |
|          | INVOICE  |                         +----+-----+          |
|          |          |<--- 1..1 --- ORDER      | CATEGORY |          |
|          +----------+                         |  (self-  |          |
|                                               |   ref)   |          |
|                                               +----------+          |
|                                                                     |
|  LEGEND:                                                            |
|  -----------                                                        |
|  ------>  =  direction of foreign key                               |
|  1    *   =  one-to-many                                            |
|  *    *   =  many-to-many (join table)                              |
|  1    1   =  one-to-one                                             |
|                                                                     |
+=====================================================================+
```

### Relationship detail table

For every relationship, also produce:

```
+--------------------------------------------------------------------+
|                    RELATIONSHIP DETAILS                             |
+--------------------------------------------------------------------+
| From     | Rel         | To         | Cascade | Fetch | Join       |
|----------|-------------|------------|---------|-------|------------|
| User     | @OneToMany  | Order      | ALL     | LAZY  | user_id   |
| Order    | @ManyToOne  | User       | --      | EAGER | user_id FK|
| User     | @ManyToMany | Role       | --      | LAZY  | user_roles|
| Order    | @OneToOne   | Invoice    | ALL     | LAZY  | order_id  |
| Order    | @OneToMany  | OrderItem  | ALL+ORP | LAZY  | order_id  |
| OrderItem| @ManyToOne  | Product    | --      | EAGER | product_id|
| Product  | @ManyToOne  | Category   | --      | LAZY  | cat_id    |
| Category | @ManyToOne  | Category   | --      | LAZY  | parent_id |
+--------------------------------------------------------------------+
```

### Cascade & Fetch Heatmap

```
+===================================================================+
|                  CASCADE / FETCH RISK HEATMAP                     |
+===================================================================+
|                                                                   |
|  Entity       | CASCADE ALL? | EAGER fetch?  | orphanRemoval?    |
|  -------------|--------------|---------------|-------------------  |
|  User->Order  |  [!!] YES    |  [  ] No      |  [  ] No          |
|  Order->Items |  [!!] YES    |  [  ] No      |  [!!] YES         |
|  Order->User  |  [  ] No     |  [!!] YES     |  [  ] No          |
|  Item->Product|  [  ] No     |  [!!] YES     |  [  ] No          |
|                                                                   |
|  [!!] = Potential risk -- Review carefully                        |
|  [  ] = OK                                                        |
|                                                                   |
|  COMMON ISSUES TO WATCH:                                          |
|  * N+1 Queries  : @OneToMany EAGER or missing JOIN FETCH         |
|  * Cascade traps: CascadeType.ALL on non-owning side             |
|  * Orphan delete: orphanRemoval=true with shared entities        |
|  * Bidirectional: Both sides must sync (addChild / setParent)    |
|                                                                   |
+===================================================================+
```

## Step 4: Analyze database migrations — Timeline Visual

If Flyway or Liquibase is present, list all migration files. Produce a **Migration Timeline**:

```
+=====================================================================+
|                    MIGRATION TIMELINE                                |
+=====================================================================+
|                                                                     |
|  V1.0           V1.1           V1.2           V2.0          V2.1   |
|   |              |              |              |              |     |
|   v              v              v              v              v     |
|  -o--------------o--------------o--------------o--------------o->  |
|   |              |              |              |              |     |
|   |  users,      |  orders      |  status      | products,   | idx:|
|   |  roles       |  table       |  enum->str   | categories  | crt |
|   |  [DDL]       |  [DDL]       |  [DDL+DML]   | [DDL]       |[DDL]|
|   |              |              |              |              |     |
|   2022-01       2022-03        2022-04        2023-01       2023-06|
|                                                                     |
|  [DDL] = Schema change    [DML] = Data migration                   |
|  [DDL+DML] = Both         [!!] = Destructive (drop col/table)      |
|                                                                     |
+=====================================================================+
```

Flag destructive migrations with `[!!]` marker.

## Step 5: Analyze repository and query patterns

For each Spring Data repository, document type, derived queries, JPQL, native queries, Specifications, and projections.

```
+=====================================================================+
|                  REPOSITORY & QUERY MAP                             |
+=====================================================================+
|                                                                     |
|  UserRepository  [JpaRepository<User, Long>]                       |
|  |                                                                  |
|  |-- findByEmail(String)                [Derived Query]             |
|  |-- findByStatusIn(List<Status>)       [Derived Query]             |
|  |-- findActiveUsersWithOrders()        [@Query JPQL]               |
|  +-- searchByName(String)              [@Query NATIVE] [!!]        |
|                                                                     |
|  OrderRepository  [JpaRepository<Order, Long>]                     |
|  |                                                                  |
|  |-- findByUserId(Long, Pageable)       [Derived Query]             |
|  |-- findByStatusAndDateRange(...)      [Specification]             |
|  +-- getOrderSummary(Long)             [@Query JPQL, Projection]   |
|                                                                     |
|  ProductRepository  [JpaRepository<Product, Long>]                 |
|  |                                                                  |
|  |-- findByCategoryId(Long)             [Derived Query]             |
|  +-- searchByNameOrSku(String)         [@Query JPQL]               |
|                                                                     |
|  [!!] = Native query -- portability concern                        |
|                                                                     |
+=====================================================================+
```

## Step 6: Produce the Data Flow Diagram

Show how data flows from React form through API to database and back:

```
+=====================================================================+
|                     DATA FLOW DIAGRAM                               |
+=====================================================================+
|                                                                     |
|  REACT FORM                    SPRING BOOT                DATABASE  |
|  (Create Order)                                                     |
|                                                                     |
|  +------------------+    +------------------+                       |
|  | OrderForm.tsx    |    | OrderController  |                       |
|  | {                |    | .createOrder()   |                       |
|  |  productId: 42,  |--->| @Valid           |                       |
|  |  quantity: 2,    |    | @RequestBody     |                       |
|  |  address: {...}  |    | CreateOrderReq   |                       |
|  | }                |    +--------+---------+                       |
|  +------------------+             |                                 |
|                                   v                                 |
|                          +--------+---------+                       |
|                          | OrderService     |                       |
|                          | .create()        |                       |
|                          | - validate stock |                       |
|                          | - calc price     |                       |
|                          | - build entity   |                       |
|                          +--------+---------+                       |
|                                   |                                 |
|              +--------------------+--------------------+            |
|              |                    |                    |             |
|              v                    v                    v             |
|  +-----------+------+  +---------+--------+  +--------+---------+  |
|  | OrderRepository  |  | OrderItemRepo    |  | ProductRepo      |  |
|  | .save(order)     |  | .saveAll(items)  |  | .findById(42)    |  |
|  +--------+---------+  +--------+---------+  +--------+---------+  |
|           |                      |                     |            |
|           v                      v                     v            |
|  +--------+---------+  +--------+---------+  +--------+---------+  |
|  | orders           |  | order_items      |  | products         |  |
|  | +id, user_id,    |  | +id, order_id,   |  | (read only)      |  |
|  |  status, total   |  |  product_id, qty |  |                  |  |
|  +------------------+  +------------------+  +------------------+  |
|                                                                     |
|           +--- RESPONSE FLOW (reverse) --->                        |
|           |                                                         |
|           v                                                         |
|  +------------------+    +------------------+    +--------------+   |
|  | Order entity     |--->| OrderResponse    |--->| React State  |   |
|  | (JPA managed)    |    | (DTO mapping)    |    | (update UI)  |   |
|  +------------------+    +------------------+    +--------------+   |
|                                                                     |
+=====================================================================+
```

## Step 7: Produce the data model document

Combine all findings into a document starting with a **Summary Dashboard**:

```
+==============================================================+
|             DATA MODEL -- {Project Name}                     |
+============================+=================================+
| Entities: 6               | Database: PostgreSQL 15          |
| Tables: 7 (incl. join)    | ORM: Hibernate 6.x              |
| Migrations: 12            | Migration: Flyway                |
+============================+=================================+
|                                                               |
|  Entity Count by Relationships      Table Size Estimate       |
|  ----------------------------       ---------------------     |
|  User        ####---- 4 rels        users       ~10K rows    |
|  Order       ######-- 5 rels        orders      ~100K rows   |
|  Product     ##------ 2 rels        products    ~5K rows     |
|  OrderItem   ###----- 3 rels        order_items ~500K rows   |
|  Category    ##------ 2 rels        categories  ~200 rows    |
|  Role        #------- 1 rel         roles       ~5 rows      |
|                                                               |
+===============================================================+
```

Followed by sections:

1. **Persistence Strategy Overview** (visual)
2. **Entity Cards** (all entities with columns)
3. **ER Diagram** (relationship map)
4. **Cascade/Fetch Heatmap** (risk indicators)
5. **Migration Timeline** (visual)
6. **Repository & Query Map** (tree)
7. **Data Flow Diagram** (React to DB and back)
8. **QA Data Considerations** — test data setup, dependencies between entities

## Tips for legacy codebases

- Look for raw JDBC usage (`JdbcTemplate`, `NamedParameterJdbcTemplate`) alongside JPA — indicates incremental modernization
- Check for stored procedures called from Java (`@Procedure`, `@NamedStoredProcedureQuery`)
- Watch for Hibernate XML mappings (`*.hbm.xml`) instead of annotations — very legacy
- Note `@Formula` and `@Where` annotations — these embed SQL that QA should understand
- Check if `ddl-auto=update` is used in production configs — this is a risk flag
- Look for `@Converter` / `AttributeConverter` — custom type mappings that affect data interpretation
- In the Entity Cards, mark legacy patterns with `[LEGACY]` flag
