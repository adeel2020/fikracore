---
id: metadata-first-document-answering
title: Metadata-First Document Answering
engine: knowledge_base
services:
  - document_catalog
  - vector_retrieval
connectors:
  - metadata_db
  - vector_db
  - microsoft_office
fcaps_lens: []
output_modes:
  - text
  - voice
requires_approval: false
---

# Metadata-First Document Answering

Use this skill when the user asks about documents, knowledge base inventory, or a specific document.

Start with the document catalog. Answer count, list, owner, type, freshness, and high-level summary questions without vector retrieval.

Only fetch vector chunks when the user asks for document content, detailed explanation, comparison, or evidence-backed answer. When using chunks, cite the source document and chunk references.

If the user asks an ambiguous document question, ask a narrowing question before retrieving chunks.
