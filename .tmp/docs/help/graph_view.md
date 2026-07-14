# Visualizing the Knowledge Graph

Here are the built-in ways to visualize your generated code knowledge graph, depending on the tool you want to use.

---

## 1. Interactive D3.js Collapsible Tree (Web Browser)

Generate an interactive, browser-loadable D3.js collapsible tree of your codebase. This creates a clean hierarchical breakdown of all files, folders, and code symbols.

* **Command:** Run this in your terminal:
  ```bash
  graphify tree
  ```
* **Output:** This generates `graphify-out/GRAPH_TREE.html`.
* **Usage:** Open `graphify-out/GRAPH_TREE.html` directly in any web browser. You can click, collapse, expand, and hover to inspect relationships.

---

## 2. Obsidian Vault (3D Navigable Network Graph)

Open the graph as a Markdown wiki directly in **Obsidian** to explore an interactive 3D graph view of the file relations and semantic communities.

* **Step 1:** Download and install [Obsidian](https://obsidian.md/).
* **Step 2:** Open Obsidian and select **"Open folder as vault"**.
* **Step 3:** Choose the `graphify-out/wiki/` directory from this project.
* **Step 4:** Open Obsidian's **Graph View** (shortcut: `Cmd + G` or `Ctrl + G`) to see a beautiful, interactive node-link visualization of your entire codebase structure.

---

## 3. Gephi / yEd (Professional Network Visualization)

For advanced graph layouts, node sizing by centrality, and complex styling, you can export the graph to the standard GraphML format.

* **Export Command:** Run:
  ```bash
  graphify export --graphml
  ```
* **Output:** Generates `graphify-out/graph.graphml`.
* **Usage:** Import `graph.graphml` directly into [Gephi](https://gephi.org/) or [yEd Graph Editor](https://www.yworks.com/products/yed) to run force-directed layouts (such as ForceAtlas2).

---

## 4. Neo4j Graph Database

To query and visualize relationships (e.g., `IMPORTS`, `CALLS`, `IMPLEMENTS`) using Cypher queries and Neo4j Bloom.

* **Push Command:** Start a local Neo4j instance, then push the graph directly:
  ```bash
  graphify --neo4j-push bolt://localhost:7687
  ```
* **Usage:** Open [Neo4j Bloom](https://neo4j.com/product/bloom/) or the Neo4j Browser to traverse and inspect nodes visually.
