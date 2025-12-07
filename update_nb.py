import json
import os

file_path = "hms/hm02/assignment02.ipynb"

# Ensure we are in the right directory or use absolute path.
# The user's request showed current path \\wsl.localhost\Ubuntu\home\stasbebra2006\B251\BI-VIZ\
# but the tool requires absolute paths. `file_path` here is relative.
# I should use abs path.

file_path = "/home/stasbebra2006/B251/BI-VIZ/hms/hm02/assignment02.ipynb"
# Windows path in tool calls, but python running in WSL/Ubuntu probably?
# The user info says: \\wsl.localhost\Ubuntu\home\stasbebra2006\B251\BI-VIZ
# The `tail` failure message showed "tail: The term ... is not recognized". This implies Windows shell.
# So I should use Windows path for `writetofile` but what about python script execution?
# If I run python on windows, it needs windows path.
# `run_command` says "Shell: powershell".
# So python script will run in Windows environment.
# But the path `hms/hm02/assignment02.ipynb` is relative to CWD.
# The CWD of run_command I set to `\\wsl.localhost\Ubuntu\home\stasbebra2006\B251\BI-VIZ`.
# So relative path `hms/hm02/assignment02.ipynb` should work if python supports it.
# Wait, `hms/hm02/...`? The view file showed `\\wsl.localhost\Ubuntu\home\stasbebra2006\B251\BI-VIZ\hms\hm02\assignment02.ipynb`.
# So relative path from `BI-VIZ` root is `hms/hm02/assignment02.ipynb`.

file_path = "hms/hm02/assignment02.ipynb"

try:
    with open(file_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
except Exception as e:
    print(f"Error reading file {file_path}: {e}")
    # Try absolute path just in case
    file_path = r"\\wsl.localhost\Ubuntu\home\stasbebra2006\B251\BI-VIZ\hms\hm02\assignment02.ipynb"
    with open(file_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

new_cells = [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "## 1. Data Preprocessing\n",
        "\n",
        "Adjusting times (modulo 24h) and loading GPS coordinates from `stops.txt`."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# Fix times > 24:00:00\n",
        "def fix_time(t_str):\n",
        "    try:\n",
        "        parts = list(map(int, t_str.split(':')))\n",
        "        parts[0] = parts[0] % 24\n",
        "        return f\"{parts[0]:02d}:{parts[1]:02d}:{parts[2]:02d}\"\n",
        "    except:\n",
        "        return t_str\n",
        "\n",
        "# Apply corrections\n",
        "d['depart_from'] = d['depart_from'].apply(fix_time)\n",
        "d['arrive_to'] = d['arrive_to'].apply(fix_time)\n",
        "\n",
        "print(\"Times fixed.\")"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# Load stops and aggregate coords\n",
        "try:\n",
        "    stops = pd.read_csv('stops.txt')\n",
        "    # Group by stop_name (handling duplicates by averaging position)\n",
        "    stop_positions = stops.groupby('stop_name')[['stop_lat', 'stop_lon']].mean()\n",
        "    pos_dict = {name: (row['stop_lon'], row['stop_lat']) for name, row in stop_positions.iterrows()}\n",
        "    print(f\"Loaded {len(pos_dict)} unique stop positions.\")\n",
        "except FileNotFoundError:\n",
        "    print(\"stops.txt not found. Please ensure it is in the same directory.\")\n",
        "    pos_dict = {}"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "## 2. Network Representation\n",
        "\n",
        "Creating a directed graph where nodes are stops and edges are connections. Weight is the frequency."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# Count frequency of each connection\n",
        "connections = d.groupby(['stop_from_name', 'stop_to_name', 'route_type']).size().reset_index(name='weight')\n",
        "\n",
        "import networkx as nx\n",
        "G = nx.DiGraph()\n",
        "\n",
        "for _, row in connections.iterrows():\n",
        "    G.add_edge(row['stop_from_name'], row['stop_to_name'], weight=row['weight'], route_type=row['route_type'])\n",
        "\n",
        "print(f\"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.\")"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "## 3. Visualization\n",
        "\n",
        "Visualizing the Tram network (route_type = 0) as requested."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "import matplotlib.pyplot as plt\n",
        "\n",
        "# Subgraph for Trams (0)\n",
        "tram_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('route_type') == 0]\n",
        "G_tram = G.edge_subgraph(tram_edges).copy()\n",
        "\n",
        "plt.figure(figsize=(12, 12))\n",
        "# Get positions for nodes in subgraph\n",
        "current_pos = {n: pos_dict.get(n, (0,0)) for n in G_tram.nodes()}\n",
        "\n",
        "nx.draw_networkx_nodes(G_tram, current_pos, node_size=10, node_color='blue')\n",
        "nx.draw_networkx_edges(G_tram, current_pos, alpha=0.1, arrows=False)\n",
        "plt.title(\"Tram Network\")\n",
        "plt.axis('off')\n",
        "plt.show()"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "## 4. Centrality Measures\n",
        "\n",
        "Calculating Degree, Betweenness, and Closeness centralities for the Tram network."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "degree_cent = nx.degree_centrality(G_tram)\n",
        "# Use unweighted for betweenness to save time or weighted if topology matters more\n",
        "betweenness_cent = nx.betweenness_centrality(G_tram)\n",
        "closeness_cent = nx.closeness_centrality(G_tram)\n",
        "\n",
        "# Top 5 nodes\n",
        "def print_top5(cent_dict, name):\n",
        "    print(f\"\\nTop 5 {name}:\")\n",
        "    for n, v in sorted(cent_dict.items(), key=lambda x: x[1], reverse=True)[:5]:\n",
        "        print(f\"{n}: {v:.4f}\")\n",
        "\n",
        "print_top5(degree_cent, \"Degree Centrality\")\n",
        "print_top5(betweenness_cent, \"Betweenness Centrality\")\n",
        "print_top5(closeness_cent, \"Closeness Centrality\")"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "## 5. Visualizing Centrality\n",
        "\n",
        "Visualizing Degree Centrality on the map."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "node_sizes = [v * 1000 for v in degree_cent.values()]\n",
        "node_colors = list(degree_cent.values())\n",
        "\n",
        "plt.figure(figsize=(12, 12))\n",
        "nodes = nx.draw_networkx_nodes(G_tram, current_pos, node_size=node_sizes, node_color=node_colors, cmap=plt.cm.viridis)\n",
        "nx.draw_networkx_edges(G_tram, current_pos, alpha=0.1)\n",
        "plt.colorbar(nodes, label='Degree Centrality')\n",
        "plt.title(\"Tram Network - Degree Centrality\")\n",
        "plt.axis('off')\n",
        "plt.show()"
      ]
    },
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "## 6. Own Questions\n",
        "\n",
        "**Q1:** What is the busiest tram connection (highest weight)?\n",
        "**Q2:** Comparison of network density between Trams (0) and Metro (1).\n",
        "**Q3:** Which stop is the most important 'bridge' (Betweenness) in the Metro network?"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# Q1: Busiest connection\n",
        "try:\n",
        "    busiest_edge = max(G_tram.edges(data=True), key=lambda x: x[2]['weight'])\n",
        "    print(f\"Busiest Tram Connection: {busiest_edge[0]} -> {busiest_edge[1]} with weight {busiest_edge[2]['weight']}\")\n",
        "except ValueError:\n",
        "    print(\"Tram graph is empty.\")\n"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# Q2: Density comparison\n",
        "metro_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('route_type') == 1]\n",
        "G_metro = G.edge_subgraph(metro_edges).copy()\n",
        "\n",
        "print(f\"Tram Density: {nx.density(G_tram):.4f}\")\n",
        "print(f\"Metro Density: {nx.density(G_metro):.4f}\")"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# Q3: Metro Betweenness\n",
        "if G_metro.number_of_nodes() > 0:\n",
        "    metro_bet = nx.betweenness_centrality(G_metro)\n",
        "    print_top5(metro_bet, \"Metro Betweenness\")\n",
        "else:\n",
        "    print(\"Metro graph is empty.\")"
      ]
    }
]

nb['cells'].extend(new_cells)

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)

print("Notebook updated successfully.")
