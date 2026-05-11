#!/usr/bin/env python3
"""
JPA Entity Scanner
Scans a Java Spring Boot codebase for JPA/Hibernate entities, relationships,
and repository patterns. Outputs a JSON summary.

Usage:
    python scan_entities.py /path/to/codebase/root

Requirements: Python 3.8+, no external dependencies.
"""

import os
import re
import json
import sys
from pathlib import Path
from collections import defaultdict


def find_java_files(root: str) -> list[Path]:
    """Recursively find Java source files (excluding test directories)."""
    exclude = {"node_modules", ".git", "target", "build", "dist", ".gradle", "test"}
    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for f in filenames:
            if f.endswith(".java"):
                results.append(Path(dirpath) / f)
    return results


def extract_entity_info(filepath: Path, content: str) -> dict | None:
    """Extract JPA entity information from a Java file."""
    if not re.search(r'@Entity\b|@Document\b', content):
        return None

    # Extract class name
    class_match = re.search(r'public\s+class\s+(\w+)', content)
    if not class_match:
        return None

    entity = {
        "name": class_match.group(1),
        "file": str(filepath),
        "annotations": [],
        "fields": [],
        "relationships": [],
    }

    # Table name
    table_match = re.search(r'@Table\s*\(\s*name\s*=\s*"(\w+)"', content)
    if table_match:
        entity["table_name"] = table_match.group(1)

    # Document annotation (MongoDB)
    if re.search(r'@Document', content):
        entity["annotations"].append("@Document")
        doc_match = re.search(r'@Document\s*\(\s*collection\s*=\s*"(\w+)"', content)
        if doc_match:
            entity["collection_name"] = doc_match.group(1)
    else:
        entity["annotations"].append("@Entity")

    # Key annotations
    for ann in ["@MappedSuperclass", "@Inheritance", "@Embeddable", "@Audited"]:
        if ann in content:
            entity["annotations"].append(ann)

    # Fields with annotations
    field_pattern = re.compile(
        r'(?:(@\w+(?:\([^)]*\))?)\s+)*'
        r'(?:private|protected)\s+'
        r'([\w<>,\s]+?)\s+'
        r'(\w+)\s*[;=]',
        re.MULTILINE
    )

    # Simpler field extraction
    lines = content.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        field_match = re.match(r'(?:private|protected)\s+([\w<>,\s?]+?)\s+(\w+)\s*[;=]', line)
        if field_match:
            field_type = field_match.group(1).strip()
            field_name = field_match.group(2)
            field_info = {"name": field_name, "type": field_type, "annotations": []}

            # Look backwards for annotations
            for j in range(max(0, i - 5), i):
                ann_line = lines[j].strip()
                ann_matches = re.findall(r'@(\w+)(?:\([^)]*\))?', ann_line)
                for a in ann_matches:
                    field_info["annotations"].append(f"@{a}")

            entity["fields"].append(field_info)

    # Relationships
    rel_patterns = {
        "@OneToMany": re.compile(r'@OneToMany\s*(?:\([^)]*\))?\s*(?:.*?\n)*?\s*(?:private|protected)\s+[\w<>,\s]+?\s+(\w+)'),
        "@ManyToOne": re.compile(r'@ManyToOne\s*(?:\([^)]*\))?\s*(?:.*?\n)*?\s*(?:private|protected)\s+[\w<>,\s]+?\s+(\w+)'),
        "@OneToOne": re.compile(r'@OneToOne\s*(?:\([^)]*\))?\s*(?:.*?\n)*?\s*(?:private|protected)\s+[\w<>,\s]+?\s+(\w+)'),
        "@ManyToMany": re.compile(r'@ManyToMany\s*(?:\([^)]*\))?\s*(?:.*?\n)*?\s*(?:private|protected)\s+[\w<>,\s]+?\s+(\w+)'),
    }

    for rel_type, pattern in rel_patterns.items():
        for match in re.finditer(rel_type.replace("@", r"@"), content):
            # Extract cascade and fetch from the annotation
            ann_end = content.find(")", match.start())
            ann_text = content[match.start():ann_end + 1] if ann_end > match.start() else ""

            cascade = "NONE"
            if "CascadeType.ALL" in ann_text:
                cascade = "ALL"
            elif "CascadeType" in ann_text:
                cascade_match = re.findall(r'CascadeType\.(\w+)', ann_text)
                cascade = ",".join(cascade_match)

            fetch = "DEFAULT"
            if "FetchType.LAZY" in ann_text:
                fetch = "LAZY"
            elif "FetchType.EAGER" in ann_text:
                fetch = "EAGER"

            orphan = "orphanRemoval" in ann_text and "true" in ann_text

            entity["relationships"].append({
                "type": rel_type,
                "cascade": cascade,
                "fetch": fetch,
                "orphan_removal": orphan,
            })

    # Audit fields
    entity["has_audit"] = bool(re.search(r'@CreatedDate|@LastModifiedDate|@CreatedBy|@LastModifiedBy', content))
    entity["has_version"] = bool(re.search(r'@Version\b', content))

    return entity


def extract_repository_info(filepath: Path, content: str) -> dict | None:
    """Extract Spring Data repository information."""
    repo_match = re.search(
        r'(?:public\s+)?interface\s+(\w+)\s+extends\s+([\w<>,\s]+)',
        content
    )
    if not repo_match:
        return None

    name = repo_match.group(1)
    extends = repo_match.group(2).strip()

    if not any(kw in extends for kw in ["Repository", "CrudRepository", "JpaRepository", "MongoRepository"]):
        return None

    repo = {
        "name": name,
        "file": str(filepath),
        "extends": extends,
        "custom_queries": [],
    }

    # Count query methods
    derived = re.findall(r'(?:List|Optional|Page|Slice|Stream|Long|int|boolean|void)\s*<?[\w<>,\s]*>?\s+(findBy\w+|countBy\w+|deleteBy\w+|existsBy\w+)', content)
    repo["derived_query_count"] = len(derived)

    jpql = re.findall(r'@Query\s*\(\s*"(?!.*nativeQuery)', content)
    repo["jpql_query_count"] = len(jpql)

    native = re.findall(r'@Query\s*\(.*nativeQuery\s*=\s*true', content)
    repo["native_query_count"] = len(native)

    procedure = re.findall(r'@Procedure', content)
    repo["stored_procedure_count"] = len(procedure)

    return repo


def detect_persistence_strategy(root: str) -> dict:
    """Detect ORM, database, and migration tool from config files."""
    strategy = {
        "orm": "unknown",
        "database": "unknown",
        "migration_tool": "none",
        "connection_pool": "unknown",
    }

    # Check build files
    for name in ["pom.xml", "build.gradle", "build.gradle.kts"]:
        for dirpath, _, filenames in os.walk(root):
            if name in filenames:
                content = (Path(dirpath) / name).read_text(errors="ignore")
                if "spring-boot-starter-data-jpa" in content:
                    strategy["orm"] = "JPA + Hibernate"
                elif "spring-boot-starter-data-mongodb" in content:
                    strategy["orm"] = "MongoDB"
                elif "mybatis" in content:
                    strategy["orm"] = "MyBatis"
                elif "spring-jdbc" in content:
                    strategy["orm"] = "Spring JDBC"

                if "flyway" in content:
                    strategy["migration_tool"] = "Flyway"
                elif "liquibase" in content:
                    strategy["migration_tool"] = "Liquibase"

                if "postgresql" in content:
                    strategy["database"] = "PostgreSQL"
                elif "mysql" in content:
                    strategy["database"] = "MySQL"
                elif "oracle" in content:
                    strategy["database"] = "Oracle"
                elif "h2" in content:
                    strategy["database"] = "H2"
                elif "mongodb" in content:
                    strategy["database"] = "MongoDB"
                break

    # Check application config
    for cfg_name in ["application.yml", "application.yaml", "application.properties"]:
        for dirpath, _, filenames in os.walk(root):
            if cfg_name in filenames:
                content = (Path(dirpath) / cfg_name).read_text(errors="ignore")
                if "ddl-auto" in content:
                    ddl_match = re.search(r'ddl-auto\s*[:=]\s*(\w+)', content)
                    if ddl_match:
                        strategy["ddl_auto"] = ddl_match.group(1)
                if "hikari" in content.lower():
                    strategy["connection_pool"] = "HikariCP"
                break

    return strategy


def count_migrations(root: str) -> dict:
    """Count migration files."""
    flyway_pattern = re.compile(r'^V[\d._]+__.*\.sql$')
    liquibase_patterns = ["changelog", "changeset"]

    flyway_count = 0
    liquibase_count = 0

    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if flyway_pattern.match(f):
                flyway_count += 1
            if any(p in f.lower() for p in liquibase_patterns) and f.endswith((".xml", ".yaml", ".yml", ".sql")):
                liquibase_count += 1

    return {
        "flyway_migrations": flyway_count,
        "liquibase_changesets": liquibase_count,
    }


def scan(root: str) -> dict:
    """Main scan function."""
    root = os.path.abspath(root)
    java_files = find_java_files(root)

    entities = []
    repositories = []

    for f in java_files:
        try:
            content = f.read_text(errors="ignore")

            entity = extract_entity_info(f, content)
            if entity:
                entities.append(entity)

            repo = extract_repository_info(f, content)
            if repo:
                repositories.append(repo)
        except IOError:
            continue

    persistence = detect_persistence_strategy(root)
    migrations = count_migrations(root)

    # Compute relationship summary
    rel_summary = defaultdict(int)
    cascade_risks = []
    for e in entities:
        for r in e["relationships"]:
            rel_summary[r["type"]] += 1
            if r["cascade"] == "ALL":
                cascade_risks.append(f"{e['name']}: {r['type']} with CASCADE ALL")
            if r["fetch"] == "EAGER":
                cascade_risks.append(f"{e['name']}: {r['type']} with EAGER fetch")

    return {
        "root": root,
        "persistence_strategy": persistence,
        "entities": {
            "count": len(entities),
            "details": entities,
        },
        "repositories": {
            "count": len(repositories),
            "details": repositories,
        },
        "relationships": {
            "summary": dict(rel_summary),
            "total": sum(rel_summary.values()),
        },
        "risks": {
            "cascade_and_fetch_warnings": cascade_risks,
        },
        "migrations": migrations,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scan_entities.py /path/to/codebase")
        sys.exit(1)

    result = scan(sys.argv[1])
    print(json.dumps(result, indent=2, default=str))
