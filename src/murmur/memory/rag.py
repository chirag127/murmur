import os
from typing import List

import chromadb
import pathspec

from murmur.state import TaskSpec


class RAGIndex:
    """
    ChromaDB index over the codebase.
    Lazily built on first use.
    Respects .gitignore via pathspec.
    """

    def __init__(self, db_path: str, repo_path: str):
        self.db_path = db_path
        self.repo_path = repo_path
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection("murmur_codebase")
        self._is_built = False

    def _get_ignore_spec(self) -> pathspec.PathSpec:
        """Parse .gitignore."""
        ignore_path = os.path.join(self.repo_path, ".gitignore")
        if not os.path.exists(ignore_path):
            return pathspec.PathSpec([])

        with open(ignore_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Add basic exclusions
        lines.extend([".git/", ".murmur/", "__pycache__/"])
        return pathspec.PathSpec.from_lines("gitwildmatch", lines)

    async def build(self, max_files: int = 1000) -> None:
        """Walk repo, chunk files, embed, insert into ChromaDB."""
        if self._is_built:
            return

        spec = self._get_ignore_spec()
        count = 0

        # NOTE: A naive build strategy.
        # Should realistically be batched + semantic chunked.
        for root, dirs, files in os.walk(self.repo_path):
            # Prune hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.repo_path)

                if spec.match_file(rel_path):
                    continue

                if count >= max_files:
                    break

                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        text = f.read()

                    if not text.strip():
                        continue

                    # Basic 1000-char chunks
                    chunks = [text[i : i + 1000] for i in range(0, len(text), 1000)]
                    ids = [f"{rel_path}_{i}" for i in range(len(chunks))]
                    metadatas = [{"path": rel_path} for _ in range(len(chunks))]

                    self.collection.add(ids=ids, documents=chunks, metadatas=metadatas)
                    count += 1
                except UnicodeDecodeError:
                    pass  # Skip binaries

        self._is_built = True

    async def query(self, query_text: str, top_k: int = 10) -> List[str]:
        if not self._is_built:
            await self.build()

        # Returns chunks that semantically match the query
        results = self.collection.query(query_texts=[query_text], n_results=top_k)

        documents = results.get("documents", [[]])[0]
        return documents

    def get_context_for_task(self, task: TaskSpec) -> str:
        """
        Produce a string of relevant code chunks to inject into system prompt.
        """
        if not self._is_built:
            return ""  # Defer to asyncio if strictly async

        # Simplified synchronous fetch:
        results = self.collection.query(
            query_texts=[task.title + " " + task.description], n_results=5
        )

        docs = results.get("documents", [[]])[0]
        return "\n\n---\n\n".join(docs)
