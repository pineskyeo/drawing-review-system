"""Stage 2: RAG 검색 — 위반 후보에 대해 관련 규칙 Top-K 검색.

ChromaDB + BGE-M3(또는 sentence-transformers 호환 모델)로
위반 항목의 컨텍스트에 가장 관련 있는 규칙을 검색한다.

Usage:
    python scripts/review/rag_search.py \
        --violations data/cache/violations.json \
        --vault standards-vault \
        --output data/cache/rag_results.json \
        --top-k 5
"""

import json
import sys
from pathlib import Path

import click
import frontmatter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.common.config import VAULT_PATH, DATA_PATH


def _get_chroma_client():
    import chromadb
    db_path = str(DATA_PATH / "chroma_db")
    return chromadb.PersistentClient(path=db_path)


def _get_embedding_fn(model_name="BAAI/bge-m3"):
    """sentence-transformers 기반 임베딩 함수."""
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    return SentenceTransformerEmbeddingFunction(model_name=model_name)


def build_index(vault_path, model_name="BAAI/bge-m3"):
    """vault의 모든 규칙을 ChromaDB에 인덱싱."""
    rules_dir = Path(vault_path) / "10-Rules"
    if not rules_dir.exists():
        click.echo("Rules directory not found")
        return

    ef = _get_embedding_fn(model_name)
    client = _get_chroma_client()

    # 기존 컬렉션 삭제 후 재생성
    try:
        client.delete_collection("rules")
    except Exception:
        pass
    collection = client.get_or_create_collection("rules", embedding_function=ef)

    docs = []
    ids = []
    metadatas = []

    for md_file in sorted(rules_dir.glob("*.md")):
        try:
            post = frontmatter.load(str(md_file))
        except Exception:
            continue

        rule_id = post.metadata.get("rule_id", md_file.stem)
        title = post.metadata.get("title", "")
        status = post.metadata.get("status", "")
        rule_type = post.metadata.get("type", "")
        severity = post.metadata.get("severity", "")
        categories = post.metadata.get("category", [])

        # 인덱싱할 텍스트: 제목 + 카테고리 + 본문
        doc_text = f"{rule_id} {title}\n카테고리: {', '.join(categories)}\n{post.content[:1000]}"

        docs.append(doc_text)
        ids.append(rule_id)
        metadatas.append({
            "rule_id": rule_id,
            "title": title,
            "status": status,
            "type": rule_type,
            "severity": severity,
            "file": str(md_file.name),
        })

    if docs:
        collection.add(documents=docs, ids=ids, metadatas=metadatas)
        click.echo(f"Indexed {len(docs)} rules into ChromaDB")

    return collection


def search_related_rules(query, top_k=5, model_name="BAAI/bge-m3"):
    """쿼리에 관련된 규칙 Top-K 검색."""
    ef = _get_embedding_fn(model_name)
    client = _get_chroma_client()

    try:
        collection = client.get_collection("rules", embedding_function=ef)
    except Exception:
        click.echo("Index not found. Run with --build-index first.")
        return []

    results = collection.query(query_texts=[query], n_results=top_k)

    related = []
    if results and results["ids"]:
        for i, rid in enumerate(results["ids"][0]):
            related.append({
                "rule_id": rid,
                "distance": results["distances"][0][i] if results.get("distances") else None,
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                "document_preview": (results["documents"][0][i][:200]
                                     if results.get("documents") else ""),
            })

    return related


def enrich_violations(violations_data, top_k=5, model_name="BAAI/bge-m3"):
    """위반 항목에 관련 규칙 컨텍스트를 추가."""
    violations = violations_data.get("violations", [])

    enriched = []
    for v in violations:
        query = f"{v.get('message', '')} {v.get('source_entity', '')} {v.get('location', '')}"
        related = search_related_rules(query, top_k=top_k, model_name=model_name)
        enriched.append({
            **v,
            "related_rules": related,
        })

    return {
        **violations_data,
        "violations": enriched,
        "rag_enriched": True,
    }


@click.command()
@click.option("--violations", default="", help="Violations JSON to enrich")
@click.option("--vault", default=str(VAULT_PATH), help="Vault path")
@click.option("--output", default="", help="Output JSON path")
@click.option("--top-k", default=5, help="Top-K results per query")
@click.option("--build-index", "build_index_flag", is_flag=True, help="Build/rebuild the vector index")
@click.option("--model", default="BAAI/bge-m3", help="Embedding model name")
@click.option("--query", default="", help="Ad-hoc query for testing")
def main(violations, vault, output, top_k, build_index_flag, model, query):
    """Stage 2: RAG 검색."""
    if build_index_flag:
        build_index(vault, model_name=model)
        return

    if query:
        results = search_related_rules(query, top_k=top_k, model_name=model)
        for r in results:
            click.echo(f"  [{r['rule_id']}] dist={r['distance']:.4f} {r['metadata'].get('title', '')}")
        return

    if not violations:
        click.echo("Provide --violations or --build-index or --query")
        return

    with open(violations, encoding="utf-8") as f:
        violations_data = json.load(f)

    enriched = enrich_violations(violations_data, top_k=top_k, model_name=model)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(enriched, f, ensure_ascii=False, indent=2)
        click.echo(f"Enriched output: {out_path}")
    else:
        click.echo(json.dumps(enriched, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
