# Local Code Intelligence Engine (LCIE)

## 1. Overview

**LCIE** is a local-first system designed to provide relevant, up-to-date code context to Large Language Models (LLMs) efficiently, with the intent of integrating directly into code editors (e.g., AI-assisted editors) as a context engine. The system avoids repeatedly scanning the entire codebase by maintaining a local index and retrieving only the most relevant code snippets per query, thereby minimizing token usage and latency during interactive development.

---

## 2. Goals

### Primary Goals

- Provide highly relevant code context to LLMs
- Minimize token usage
- Ensure context freshness with minimal latency

### Secondary Goals

- Work locally without requiring centralized infrastructure
- Scale to large multi-repo workspaces
- Be extensible for future intelligence features

---

## 3. Non-Goals

- Building a full IDE or code editor
- Perfect semantic understanding of code
- Replacing static analysis tools or compilers

---

## 4. System Architecture

### Components

1. **Indexer**

   - Chunks code into logical units (functions/classes)
   - Generates embeddings
   - Stores metadata

2. **Vector Store**

   - Stores embeddings and metadata
   - Supports similarity search

3. **Keyword/Symbol Search Engine**

   - Provides exact matches (e.g., grep, AST-based search)

4. **Retrieval Engine**

   - Combines semantic and keyword results
   - Ranks and merges results
   - Expands context (neighbors, imports)

5. **Context Assembler**

   - Builds final prompt context
   - Deduplicates and trims content

6. **LLM Interface**

   - Sends query + context to model
   - Returns response

7. **File Watcher**

   - Detects file changes
   - Triggers incremental re-indexing

---

## 5. Data Flow

### Indexing Flow

1. Scan codebase
2. Chunk into units
3. Generate embeddings
4. Store in vector DB with metadata

### Query Flow

1. User submits query
2. Embed query
3. Retrieve top semantic matches
4. Retrieve keyword/symbol matches
5. Merge and rank results
6. Expand context
7. Assemble prompt
8. Send to LLM

### Update Flow

1. File change detected
2. Re-chunk affected file
3. Recompute embeddings
4. Update index

---

## 6. Data Model

Each chunk stores:

- file\_path
- content
- embedding
- hash
- start\_line
- end\_line
- symbols (optional)
- last\_updated

---

## 7. Retrieval Strategy

### Hybrid Retrieval

- Semantic search (embeddings)
- Keyword search (exact matches)

### Ranking

We use a hybrid scoring function that combines semantic similarity, keyword/symbol match, and Git-based recency into a single normalized score.

#### Final Score

```
score = w_s * S_sem + w_k * S_kw + w_g * S_git - w_d * penalty_dup
```

Where:
- `S_sem` = semantic similarity score (embedding cosine similarity, normalized to [0,1])
- `S_kw` = keyword/symbol match score (exact match strength, normalized to [0,1])
- `S_git` = recency score derived from Git signals (normalized to [0,1])
- `penalty_dup` = penalty for redundant or overlapping chunks
- `w_s, w_k, w_g, w_d` = tunable weights (sum of primary weights ≈ 1)

---

#### 1. Semantic Score (S_sem)

- Computed using cosine similarity between query and chunk embeddings
- Normalize to [0,1]
- Captures intent and meaning

---

#### 2. Keyword/Symbol Score (S_kw)

Heuristic scoring:

```
S_kw = 1.0 (exact symbol match)
     = 0.7 (partial match / substring)
     = 0.4 (filename match)
     = 0.0 (no match)
```

Enhancements:
- Boost if query token matches function/class name
- Boost repeated matches within chunk

---

#### 3. Git Recency Score (S_git)

Derived from how recently the chunk/file was modified.

```
S_git = exp(-lambda * age_in_days)
```

Where:
- `age_in_days` = time since last modification
- `lambda` controls decay rate (e.g., 0.1–0.3)

Additional boosts:
- +0.2 if in current uncommitted diff
- +0.1 if part of recent commits (last N commits)

Clamp final value to [0,1]

---

#### 4. Duplicate / Redundancy Penalty

Reduce score for:
- Overlapping chunks from same file
- Repeated retrievals across iterations

```
penalty_dup = overlap_ratio
```

---

#### 5. Suggested Default Weights

```
w_s = 0.5   (semantic is primary)
w_k = 0.3   (exact matches are critical for code)
w_g = 0.2   (recency bias)
w_d = 0.1   (penalty strength)
```

These should be configurable and tunable based on usage.

---

#### 6. Post-ranking Refinement

After scoring:

- Select top-K chunks (e.g., 5–10)
- Ensure diversity (avoid same-file dominance)
- Expand context (neighbors, imports)

---

### Context Expansion

- Include neighboring code
- Include imports
- Include related symbols

---

## 8. Freshness Strategy

### Incremental Updates

- Triggered on file save or git changes
- Only update changed chunks

### Git-Aware Updates (Key Enhancement)

The system integrates with Git to perform precise **embedding invalidation and updates**, avoiding full re-indexing.

#### Core Idea: Diff-Based Invalidation

Instead of re-indexing entire files, we use `git diff` to identify exactly what changed.

Workflow:

1. Run `git diff` (working tree or against HEAD)
2. Extract changed file paths and line ranges
3. Map changed lines to existing chunks (via start_line / end_line)
4. Invalidate only affected chunks
5. Re-chunk and re-embed only those regions

This ensures:
- Minimal recomputation
- High freshness
- Efficient updates

---

#### Handling Different Change Types

- **Modified files** → Partial chunk invalidation via diff mapping
- **New files** → Full chunking + embedding
- **Deleted files** → Remove associated chunks from index
- **Renamed files** → Update metadata without re-embedding (if content unchanged)

---

#### Edge Cases & Safeguards

- Large diffs (e.g., formatting changes):
  - Fallback to full file re-index
- Complex refactors (function moves):
  - Re-chunk entire file
- Dirty working directory:
  - Use `git status` + fallback to file watcher

---

#### Periodic Validation (Optional)

Even with diff-based updates, periodic validation can help:

- Recompute hashes for indexed chunks
- Detect silent drift
- Trigger selective re-index if mismatch found

---

### Git-Based Context Retrieval

Git can also be used during query time:

- Retrieve recent changes (`git diff HEAD`)
- Include commit history for context
- Answer questions like:
  - "What changed recently?"
  - "What might this commit break?"

### Hash-based Validation

- Avoid re-embedding unchanged content

### Runtime Validation

- Re-read file content before sending to LLM
- Replace stale chunks if needed

---

## 9. Efficiency Optimizations

- Chunk-level indexing
- Debounced updates
- Session-level caching
- Limit top-K retrieval

### Handling Auto-Save / High-Frequency Changes

Modern editors (e.g., auto-save) can trigger very frequent file change events. LCIE must avoid re-embedding on every save.

#### Debounce + Batch Strategy (Primary Mechanism)

- Collect file change events in a short window (e.g., 300–1000 ms)
- Coalesce multiple changes to the same file
- Run a single diff + re-index cycle per batch

```
On file change → add to queue
Wait debounce window → process unique files
```

#### Change Coalescing

- If the same file changes multiple times rapidly:
  - Only process the latest state
  - Skip intermediate embeddings entirely

#### Diff Thresholding

- If diff size is small → partial chunk invalidation
- If diff size is large (e.g., >30–40% of file):
  - Fallback to full file re-index

#### Priority Scheduling

- High priority: files actively being edited
- Medium: recently changed files
- Low: background validation

#### Backpressure Control

- Limit concurrent embedding jobs
- Queue excess work
- Drop redundant updates if superseded by newer changes

#### Practical Outcome

- Auto-save events do NOT cause excessive recomputation
- Embeddings are updated near-real-time but efficiently
- System remains responsive during rapid editing

---

## 10. Fallback Mechanism

### Triggers

- Low confidence retrieval
- User intent (debugging, tracing)

### Behavior

- Expand retrieval scope
- Fetch additional context progressively

---

## 11. User Interface

### CLI

- `lcie ask "<query>"`
- `lcie refresh`
- `lcie status`

### Optional UI

- File awareness panel
- Retrieved context preview

---

## 12. Trade-offs

### Pros

- Reduced token usage
- Faster responses
- Local-first design

### Cons

- Index maintenance complexity
- Retrieval tuning required
- Potential missed context

---

## 13. Future Work

- Call graph analysis
- Advanced Git integration (blame, history reasoning)
- Multi-repo indexing
- Shared team index
- Change impact analysis using Git diffs

---

## 14. Success Metrics

- Token reduction percentage
- Query latency
- Retrieval accuracy
- Developer satisfaction

---

## 15. Timeline (Rough)

### Week 1-2

- Basic indexing + retrieval

### Week 3

- Hybrid search

### Week 4

- Incremental updates + optimization

### Week 5

- Context expansion + refinement

---

## 16. Summary

**LCIE** is a context retrieval system designed to efficiently bridge large codebases and LLMs by providing relevant, fresh, and minimal context. The system prioritizes correctness and efficiency through hybrid retrieval and incremental indexing.

