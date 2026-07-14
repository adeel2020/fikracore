"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import { forceX, forceY, forceCenter, forceRadial } from "d3-force";
import { GraphNode, GraphLink } from "../types/context.types";
import { THEMES, INITIAL_NODES, INITIAL_LINKS, INTENT_WORKFLOWS } from "../components/shared/constants";

export function useContextView() {
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isFirstFitRef = useRef(true);
  const loadedRef = useRef(false);

  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;

    fetch("/trace_graph.json")
      .then((r) => {
        if (!r.ok) throw new Error("not found");
        return r.json();
      })
      .then((data) => {
        if (data?.nodes && data?.links) {
          setNodes(data.nodes);
          setLinks(data.links);
        }
      })
      .catch(() => {
        setNodes(INITIAL_NODES);
        setLinks(INITIAL_LINKS);
      })
      .finally(() => setLoading(false));
  }, []);

  const [focusedNode, setFocusedNode] = useState<GraphNode | null>(null);
  const [copied, setCopied] = useState(false);
  const [showIntentCatalog, setShowIntentCatalog] = useState(false);
  const [selectedIntentWorkflow, setSelectedIntentWorkflow] = useState<string | null>(null);
  const [copiedWorkflow, setCopiedWorkflow] = useState(false);
  const [activeTab, setActiveTab] = useState("graph");
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [selectedNodeType, setSelectedNodeType] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTheme, setActiveTheme] = useState<string>("cyberpunk");
  const [nodeStyle, setNodeStyle] = useState<
    "classic" | "glyphs" | "badges" | "geometry" | "bubble" | "crystal"
  >("classic");
  const [showThemeCatalog, setShowThemeCatalog] = useState(false);
  const [showStyleCatalog, setShowStyleCatalog] = useState(false);
  const [layoutMode, setLayoutMode] = useState<
    "standard" | "synapses" | "orbit" | "pods" | "spoke"
  >("synapses");
  const [showClusterCatalog, setShowClusterCatalog] = useState(false);
  const [uploadFormat, setUploadFormat] = useState<"json" | "markdown" | null>(null);
  const [showExportCatalog, setShowExportCatalog] = useState(false);

  const currentTheme = THEMES[activeTheme] || THEMES.cyberpunk;

  const changeLayoutMode = (mode: "standard" | "synapses" | "orbit" | "pods" | "spoke") => {
    setLayoutMode(mode);
    if (typeof window !== "undefined") {
      localStorage.setItem("tg-layout-mode", mode);
    }
  };

  const convertGraphToTriplets = (nodesList: GraphNode[], linksList: GraphLink[]): string => {
    let md = "### Ephemeral Network Graph\n\n";
    linksList.forEach((link) => {
      const sId = typeof link.source === "object" ? link.source.id : link.source;
      const sNode =
        typeof link.source === "object"
          ? link.source
          : nodesList.find((n) => n.id === sId);
      const sType = sNode?.type || "Node";

      const tId = typeof link.target === "object" ? link.target.id : link.target;
      const tNode =
        typeof link.target === "object"
          ? link.target
          : nodesList.find((n) => n.id === tId);
      const tType = tNode?.type || "Node";

      const relation = link.label || "CONNECTED_TO";

      md += `- (${sType}: ${sId}) -> [${relation}] -> (${tType}: ${tId})\n`;
    });
    return md;
  };

  const handleDownload = (format: "json" | "markdown") => {
    const activeNodes = graphData.nodes;
    const activeLinks = graphData.links;

    if (!activeNodes || activeNodes.length === 0) return;

    let content = "";
    let mimeType = "";
    let fileName = "";

    if (format === "json") {
      const cleanNodes = activeNodes.map((n: any) => ({
        id: n.id,
        label: n.label,
        type: n.type,
        ...(n.isHub ? { isHub: true, hubType: n.hubType, symbol: n.symbol } : {}),
      }));
      const cleanLinks = activeLinks.map((l: any) => ({
        source: typeof l.source === "object" ? l.source.id : l.source,
        target: typeof l.target === "object" ? l.target.id : l.target,
        label: l.label,
        ...(l.isHubLink ? { isHubLink: true } : {}),
      }));

      content = JSON.stringify({ nodes: cleanNodes, links: cleanLinks }, null, 2);
      mimeType = "application/json";
      fileName = "trace_graph.json";
    } else {
      content = convertGraphToTriplets(activeNodes, activeLinks);
      mimeType = "text/markdown";
      fileName = "trace_triplets.md";
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const linkEl = document.createElement("a");
    linkEl.href = url;
    linkEl.download = fileName;
    document.body.appendChild(linkEl);
    linkEl.click();
    document.body.removeChild(linkEl);
    URL.revokeObjectURL(url);
  };

  const triggerUpload = (format: "json" | "markdown") => {
    setUploadFormat(format);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
      fileInputRef.current.click();
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !uploadFormat) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      if (!text) return;

      try {
        if (uploadFormat === "json") {
          const parsed = JSON.parse(text);
          if (Array.isArray(parsed.nodes) && Array.isArray(parsed.links)) {
            const rawNodes = parsed.nodes.filter((n: any) => !n.isHub && !n.id.startsWith("hub_"));
            const rawLinks = parsed.links.filter(
              (l: any) =>
                !l.isHubLink &&
                !(
                  typeof l.source === "string"
                    ? l.source.startsWith("hub_")
                    : l.source.id?.startsWith("hub_")
                )
            );

            const newNodes: GraphNode[] = rawNodes.map((n: any) => ({
              id: n.id,
              label: n.label || n.id,
              type: n.type || "Node",
              ...(n.isHub ? { isHub: true, hubType: n.hubType, symbol: n.symbol } : {}),
            }));
            const newLinks: GraphLink[] = rawLinks.map((l: any) => ({
              source: typeof l.source === "object" ? l.source.id : l.source,
              target: typeof l.target === "object" ? l.target.id : l.target,
              label: l.label || "CONNECTED_TO",
              ...(l.isHubLink ? { isHubLink: true } : {}),
            }));
            setNodes(newNodes);
            setLinks(newLinks);
            setFocusedNode(null);
            isFirstFitRef.current = true;
          } else {
            alert("Invalid JSON format: Must contain 'nodes' and 'links' arrays.");
          }
        } else {
          const lines = text.split("\n");
          const parsedNodesMap = new Map<string, GraphNode>();
          const parsedLinks: GraphLink[] = [];

          const tripletRegex =
            /-\s*\(([^:]+):\s*([^\)]+)\)\s*->\s*\[([^\]]+)\]\s*->\s*\(([^:]+):\s*([^\)]+)\)/;

          const cleanLabel = (id: string) => {
            return id
              .replace(/^(intent|service|platform|precondition|error|channel|profile|apptype)_/i, "")
              .replace(/_/g, " ")
              .replace(/\b\w/g, (c) => c.toUpperCase());
          };

          lines.forEach((line) => {
            const match = line.match(tripletRegex);
            if (match) {
              const sType = match[1].trim() as any;
              const sId = match[2].trim();
              const relation = match[3].trim();
              const tType = match[4].trim() as any;
              const tId = match[5].trim();

              if (
                sType === "Hub" ||
                sId.startsWith("hub_") ||
                tType === "Hub" ||
                tId.startsWith("hub_")
              ) {
                return;
              }

              if (!parsedNodesMap.has(sId)) {
                parsedNodesMap.set(sId, {
                  id: sId,
                  label: cleanLabel(sId),
                  type: sType,
                });
              }
              if (!parsedNodesMap.has(tId)) {
                parsedNodesMap.set(tId, {
                  id: tId,
                  label: cleanLabel(tId),
                  type: tType,
                });
              }

              parsedLinks.push({
                source: sId,
                target: tId,
                label: relation,
              });
            }
          });

          if (parsedNodesMap.size > 0) {
            setNodes(Array.from(parsedNodesMap.values()));
            setLinks(parsedLinks);
            setFocusedNode(null);
            isFirstFitRef.current = true;
          } else {
            alert(
              "Invalid Markdown: No valid semantic triplets found in format '- (Type: ID) -> [Relation] -> (Type: ID)'"
            );
          }
        }
      } catch (err) {
        console.error(err);
        alert("Error parsing file. Please check file formatting.");
      }
    };
    reader.readAsText(file);
  };

  const graphData = useMemo(() => {
    if (layoutMode !== "synapses") {
      return { nodes, links };
    }

    const centerX = 0;
    const centerY = 0;

    const types = Array.from(new Set(nodes.map((n) => n.type)));
    const hubNodes: GraphNode[] = types.map((type, idx) => {
      const siblingNodes = nodes.filter(
        (n) => n.type === type && n.x !== undefined && n.y !== undefined
      );
      let initX = centerX;
      let initY = centerY;
      if (siblingNodes.length > 0) {
        const sumX = siblingNodes.reduce((sum, n) => sum + (n.x || 0), 0);
        const sumY = siblingNodes.reduce((sum, n) => sum + (n.y || 0), 0);
        initX = sumX / siblingNodes.length;
        initY = sumY / siblingNodes.length;
      }

      const hubNode: GraphNode = {
        id: `hub_${type}`,
        label: `${type} Cluster Hub`,
        type: "Hub",
        hubType: type,
        isHub: true,
        symbol: idx % 2 === 0 ? "-" : "+",
      };

      if (siblingNodes.length > 0) {
        hubNode.x = initX;
        hubNode.y = initY;
      }

      return hubNode;
    });

    const hubLinks: GraphLink[] = nodes.map((node) => ({
      source: `hub_${node.type}`,
      target: node.id,
      label: "",
      isHubLink: true,
    }));

    return {
      nodes: [...nodes, ...hubNodes],
      links: [...links, ...hubLinks],
    };
  }, [layoutMode, nodes, links]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedTheme = localStorage.getItem("tg-active-theme");
      const savedStyle = localStorage.getItem("tg-node-style");
      const savedLayout = localStorage.getItem("tg-layout-mode");
      const savedTab = localStorage.getItem("tg-active-tab");
      if (savedTheme && THEMES[savedTheme]) setActiveTheme(savedTheme);
      if (savedStyle) setNodeStyle(savedStyle as any);
      if (savedLayout) setLayoutMode(savedLayout as any);
      if (savedTab) setActiveTab(savedTab);
    }
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("tg-active-tab", activeTab);
    }
  }, [activeTab]);

  const changeTheme = (theme: string) => {
    setActiveTheme(theme);
    if (typeof window !== "undefined") {
      localStorage.setItem("tg-active-theme", theme);
    }
  };

  const changeStyle = (
    style: "classic" | "glyphs" | "badges" | "geometry" | "bubble" | "crystal"
  ) => {
    setNodeStyle(style);
    if (typeof window !== "undefined") {
      localStorage.setItem("tg-node-style", style);
    }
  };

  useEffect(() => {
    if (fgRef.current && activeTab === "graph") {
      const isFirst = isFirstFitRef.current;

      const timer1 = setTimeout(() => {
        if (fgRef.current && typeof fgRef.current.zoomToFit === "function") {
          if (isFirst) {
            fgRef.current.centerAt(0, 0, 0);
            fgRef.current.zoom(1.1, 0);
            isFirstFitRef.current = false;
          } else {
            fgRef.current.zoomToFit(150, 110);
            const currentZoom = fgRef.current.zoom();
            if (currentZoom > 1.5) fgRef.current.zoom(1.5, 0);
            else if (currentZoom < 0.75) fgRef.current.zoom(0.85, 0);
          }
        }
      }, 50);

      const timer2 = setTimeout(() => {
        if (fgRef.current && typeof fgRef.current.zoomToFit === "function") {
          if (!isFirst) {
            fgRef.current.zoomToFit(200, 110);
            const currentZoom = fgRef.current.zoom();
            if (currentZoom > 1.5) fgRef.current.zoom(1.5, 0);
            else if (currentZoom < 0.75) fgRef.current.zoom(0.85, 0);
          }
        }
      }, 350);

      const timer3 = setTimeout(() => {
        if (fgRef.current && typeof fgRef.current.zoomToFit === "function") {
          if (!isFirst) {
            fgRef.current.zoomToFit(200, 110);
            const currentZoom = fgRef.current.zoom();
            if (currentZoom > 1.5) fgRef.current.zoom(1.5, 150);
            else if (currentZoom < 0.75) fgRef.current.zoom(0.85, 150);
          }
        }
      }, 1000);

      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
      };
    }
  }, [activeTab, nodes, links]);

  useEffect(() => {
    if (!containerRef.current || activeTab !== "graph") return;

    const initialWidth = containerRef.current.clientWidth || 0;
    const initialHeight = containerRef.current.clientHeight || 0;
    if (initialWidth > 0 && initialHeight > 0) {
      setDimensions({ width: initialWidth, height: initialHeight });
    }

    const resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({
            width: width,
            height: height,
          });
        }
      }
    });

    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, [activeTab, loading]);

  useEffect(() => {
    if (!fgRef.current || activeTab !== "graph") return;

    const frameId = requestAnimationFrame(() => {
      if (!fgRef.current) return;

      fgRef.current.d3Force("center", forceCenter(0, 0));
      fgRef.current.d3Force("radial", null);

      if (layoutMode === "synapses") {
        fgRef.current.d3Force("charge")
          ?.strength((node: any) => (node.isHub ? -380 : -45))
          .distanceMax(250);

        fgRef.current.d3Force("link")
          ?.distance((link: any) => (link.isHubLink ? 45 : 130))
          .iterations(2);

        fgRef.current.d3Force("x", forceX(0).strength((node: any) => {
          if (selectedNodeType && node.type === selectedNodeType) return 0.7;
          return 0.05;
        }));
        fgRef.current.d3Force("y", forceY(0).strength((node: any) => {
          if (selectedNodeType && node.type === selectedNodeType) return 0.7;
          return 0.05;
        }));
      } else if (layoutMode === "pods") {
        const categories = [
          "Channel",
          "AppType",
          "CustomerProfile",
          "Intent",
          "Service",
          "Precondition",
          "Error",
          "Platform",
        ];
        const centerX = 0;
        const centerY = 0;
        const clusterRadius = 180;
        const podCenters: Record<string, { x: number; y: number }> = {};
        categories.forEach((cat, idx) => {
          const angle = (idx * 2 * Math.PI) / categories.length;
          podCenters[cat] = {
            x: centerX + clusterRadius * Math.cos(angle),
            y: centerY + clusterRadius * Math.sin(angle),
          };
        });

        fgRef.current.d3Force("charge")?.strength(-60).distanceMax(200);
        fgRef.current.d3Force("link")?.distance(65).iterations(2);

        fgRef.current.d3Force("x", forceX((node: any) => {
          return podCenters[node.type]?.x ?? centerX;
        }).strength(0.65));
        fgRef.current.d3Force("y", forceY((node: any) => {
          return podCenters[node.type]?.y ?? centerY;
        }).strength(0.65));
      } else if (layoutMode === "spoke") {
        const nodeDegrees: Record<string, number> = {};
        nodes.forEach((n) => {
          nodeDegrees[n.id] = 0;
        });
        links.forEach((l) => {
          const s = typeof l.source === "object" ? l.source.id : l.source;
          const t = typeof l.target === "object" ? l.target.id : l.target;
          if (nodeDegrees[s] !== undefined) nodeDegrees[s]++;
          if (nodeDegrees[t] !== undefined) nodeDegrees[t]++;
        });

        fgRef.current.d3Force("charge")?.strength(-160).distanceMax(200);

        fgRef.current.d3Force("link")
          ?.distance((link: any) => {
            const sId = typeof link.source === "object" ? link.source.id : link.source;
            const tId = typeof link.target === "object" ? link.target.id : link.target;
            const isLeafLink = nodeDegrees[sId] === 1 || nodeDegrees[tId] === 1;
            return isLeafLink ? 25 : 85;
          })
          .iterations(2);

        fgRef.current.d3Force("x", forceX(0).strength((node: any) => {
          if (selectedNodeType && node.type === selectedNodeType) return 0.7;
          return 0.05;
        }));
        fgRef.current.d3Force("y", forceY(0).strength((node: any) => {
          if (selectedNodeType && node.type === selectedNodeType) return 0.7;
          return 0.05;
        }));
      } else if (layoutMode === "orbit") {
        const TYPE_RADII: Record<string, number> = {
          Channel: 50,
          AppType: 80,
          CustomerProfile: 110,
          Intent: 145,
          Service: 180,
          Precondition: 215,
          Error: 250,
          Platform: 295,
        };

        fgRef.current.d3Force("charge")?.strength(-60).distanceMax(180);
        fgRef.current.d3Force("link")?.distance(80).iterations(2);

        fgRef.current.d3Force("radial", forceRadial((node: any) => {
          return TYPE_RADII[node.type] || 150;
        }, 0, 0).strength(0.85));

        fgRef.current.d3Force("x", null);
        fgRef.current.d3Force("y", null);
      } else {
        const chargeStrength = nodeStyle === "badges" ? -130 : -85;
        fgRef.current.d3Force("charge")?.strength(chargeStrength).distanceMax(200);

        const linkDistance = nodeStyle === "badges" ? 95 : 75;
        fgRef.current.d3Force("link")?.distance(linkDistance).iterations(2);

        fgRef.current.d3Force("x", forceX(0).strength((node: any) => {
          if (selectedNodeType && node.type === selectedNodeType) return 0.7;
          return 0.05;
        }));
        fgRef.current.d3Force("y", forceY(0).strength((node: any) => {
          if (selectedNodeType && node.type === selectedNodeType) return 0.7;
          return 0.05;
        }));
      }

      if (fgRef.current.d3Force("box")) {
        fgRef.current.d3Force("box", null);
      }

      fgRef.current.d3ReheatSimulation();
    });

    return () => cancelAnimationFrame(frameId);
  }, [activeTab, selectedNodeType, nodeStyle, layoutMode, nodes, links, dimensions]);

  const handleNodeClick = (node: any) => {
    setShowThemeCatalog(false);
    setShowStyleCatalog(false);
    setShowClusterCatalog(false);
    setShowExportCatalog(false);
    setShowIntentCatalog(false);
    setFocusedNode(node);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 800);
      fgRef.current.zoom(3, 800);
    }
  };

  const handleZoomIn = () => {
    if (fgRef.current) {
      const currentZoom = fgRef.current.zoom();
      fgRef.current.zoom(currentZoom * 1.3, 400);
    }
  };

  const handleZoomOut = () => {
    if (fgRef.current) {
      const currentZoom = fgRef.current.zoom();
      fgRef.current.zoom(currentZoom / 1.3, 400);
    }
  };

  const handleZoomToFit = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(500, 50);
    }
  };

  const toggleThemeCatalog = () => {
    setShowThemeCatalog((prev) => !prev);
    setShowStyleCatalog(false);
    setShowClusterCatalog(false);
    setShowExportCatalog(false);
    setShowIntentCatalog(false);
  };

  const toggleStyleCatalog = () => {
    setShowStyleCatalog((prev) => !prev);
    setShowThemeCatalog(false);
    setShowClusterCatalog(false);
    setShowExportCatalog(false);
    setShowIntentCatalog(false);
  };

  const toggleClusterCatalog = () => {
    setShowClusterCatalog((prev) => !prev);
    setShowThemeCatalog(false);
    setShowStyleCatalog(false);
    setShowExportCatalog(false);
    setShowIntentCatalog(false);
  };

  const toggleExportCatalog = () => {
    setShowExportCatalog((prev) => !prev);
    setShowThemeCatalog(false);
    setShowStyleCatalog(false);
    setShowClusterCatalog(false);
    setShowIntentCatalog(false);
  };

  const isLinkConnected = (link: any) => {
    if (!focusedNode) return false;
    const sourceId = typeof link.source === "object" ? link.source.id : link.source;
    const targetId = typeof link.target === "object" ? link.target.id : link.target;
    return sourceId === focusedNode.id || targetId === focusedNode.id;
  };

  const isLinkOfSelectedType = (link: any) => {
    if (!selectedNodeType) return true;
    const sourceId = typeof link.source === "object" ? link.source.id : link.source;
    const targetId = typeof link.target === "object" ? link.target.id : link.target;
    const sourceNode = nodes.find((n) => n.id === sourceId);
    const targetNode = nodes.find((n) => n.id === targetId);
    return sourceNode?.type === selectedNodeType || targetNode?.type === selectedNodeType;
  };

  const extractIntentContext = (selectedIntentNodeId: string) => {
    const intentNode = nodes.find((n) => n.id === selectedIntentNodeId);
    if (!intentNode || intentNode.type !== "Intent") return null;

    const subgraphNodes = new Set<any>();
    const subgraphLinks: any[] = [];

    subgraphNodes.add(intentNode);

    const firstHopLinks = links.filter(
      (link) => link.source === selectedIntentNodeId || link.target === selectedIntentNodeId
    );

    firstHopLinks.forEach((link) => {
      subgraphLinks.push(link);

      const neighborId = link.source === selectedIntentNodeId ? link.target : link.source;
      const neighborNode = nodes.find((n) => n.id === neighborId);

      if (neighborNode) {
        subgraphNodes.add(neighborNode);

        const secondHopLinks = links.filter(
          (l) =>
            (l.source === neighborId || l.target === neighborId) &&
            l.source !== selectedIntentNodeId &&
            l.target !== selectedIntentNodeId
        );

        secondHopLinks.forEach((l) => {
          if (
            !subgraphLinks.some(
              (existing) => existing.source === l.source && existing.target === l.target
            )
          ) {
            subgraphLinks.push(l);
          }

          const secondNeighborId = l.source === neighborId ? l.target : l.source;
          const secondNeighborNode = nodes.find((n) => n.id === secondNeighborId);
          if (secondNeighborNode) {
            subgraphNodes.add(secondNeighborNode);
          }
        });
      }
    });

    return {
      rootIntent: intentNode.label,
      extractionTimestamp: new Date().toISOString(),
      nodes: Array.from(subgraphNodes).map((n: any) => ({
        id: n.id,
        label: n.label,
        type: n.type,
      })),
      relationships: subgraphLinks.map((l: any) => ({
        source: l.source,
        target: l.target,
        relationship: l.label,
      })),
    };
  };

  const currentContextPayload = useMemo(() => {
    return focusedNode?.type === "Intent" ? extractIntentContext(focusedNode.id) : null;
  }, [focusedNode, nodes, links]);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getRoutingGuidance = (node: GraphNode) => {
    switch (node.type) {
      case "Intent":
        return {
          title: "Escalation Routing Protocol",
          heading: "Active Mobile User Complaint Dynamic:",
          advice: `This complaint represents a user-reported connectivity failure. Guide the Back-Office agent to verify connected preconditions (e.g. SIM active, VoLTE support) before routing. If preconditions are met, assign the ticket to the indicated core Platform/Team.`,
          steps: [
            "Verify subscriber balance is positive & SIM profile active.",
            "Identify signaling warnings (e.g. PLMN Forbidden, SINR Noise) connected to this intent.",
            "Refer to Core or RAN team depending on specific warning triggers.",
          ],
        };
      case "Platform":
        return {
          title: "Technical Support Escalation Target",
          heading: "Target Engineering Team Routing Info:",
          advice: `This is the technical support engineering department responsible for resolving this type of infrastructure failure. Escalate assignment tickets to this team to proceed with core database and signaling diagnostics.`,
          steps: [
            "Compile all 1-hop and 2-hop session telemetry logs.",
            "Attach the extracted LLM JSON Context Block to the ServiceNow ticket.",
            "Route ticket with High priority status in JIRA/ServiceNow.",
          ],
        };
      case "Service":
        return {
          title: "Affected Mobile Core System",
          heading: "Affected Network Sub-System Impact:",
          advice: `This is the underlying core networking system affected by the user's intent. Network errors on this service indicate core switching, packet gateways, or inter-carrier roaming trunk disruptions.`,
          steps: [
            "Monitor HSS provisioning signals and VLR registry logs.",
            "Check inter-carrier trunk link health and packet latency.",
            "Inspect error alert warning signals connected to this service.",
          ],
        };
      case "Precondition":
        return {
          title: "Agent Verification Checklist",
          heading: "Required Diagnostic Preconditions:",
          advice: `Verify that this subscriber status precondition is fully active and provisioned on the user account before routing the ticket to the core network teams.`,
          steps: [
            "Query subscriber HLR profile registry status.",
            "Verify account pre-payment balance is positive.",
            "Confirm user device model supports 5G / eSIM technologies.",
          ],
        };
      case "Error":
        return {
          title: "Signal Failure Warning",
          heading: "Diagnostic Signal Analysis:",
          advice: `This warning represents a specific network failure code detected during connection handshakes. Use this error code to speed up core engineering analysis.`,
          steps: [
            "Check core network signaling tracer logs.",
            "Identify localized cell towers or roaming trunks raising this error.",
            "Escalate to RAN or Roaming desk depending on error type.",
          ],
        };
      case "FAQ":
        return {
          title: "FAQ Support Guidance",
          heading: "Self-Service & Diagnostic Action:",
          advice: `This is a standard customer FAQ. Follow the action guidelines and verify mandatory preconditions before recommending escalation. Click the portal link below to access the official support article.`,
          steps: [
            "Verify all mandatory prechecks listed in the details.",
            "Instruct the customer on the step-by-step FAQ action.",
            "Open the corresponding support portal article for detailed reference.",
          ],
        };
      default:
        return {
          title: "Ontology Component Detail",
          heading: "Telecom Ontological Role:",
          advice: `This node represents a structural component of our telecom intent routing graph, defining the operational channels and profiles associated with customer complaints.`,
          steps: [
            "Inspect linked user intents and affected services.",
            "Determine the channel or profile context for this complaint.",
          ],
        };
    }
  };

  const guidance = useMemo(() => {
    return focusedNode ? getRoutingGuidance(focusedNode) : null;
  }, [focusedNode]);

  return {
    loading,
    fgRef,
    containerRef,
    fileInputRef,
    nodes,
    links,
    focusedNode,
    setFocusedNode,
    copied,
    showIntentCatalog,
    setShowIntentCatalog,
    selectedIntentWorkflow,
    setSelectedIntentWorkflow,
    copiedWorkflow,
    setCopiedWorkflow,
    activeTab,
    setActiveTab,
    dimensions,
    selectedNodeType,
    setSelectedNodeType,
    isExpanded,
    setIsExpanded,
    activeTheme,
    changeTheme,
    nodeStyle,
    changeStyle,
    showThemeCatalog,
    setShowThemeCatalog,
    showStyleCatalog,
    setShowStyleCatalog,
    layoutMode,
    changeLayoutMode,
    showClusterCatalog,
    setShowClusterCatalog,
    showExportCatalog,
    setShowExportCatalog,
    handleDownload,
    triggerUpload,
    handleFileUpload,
    graphData,
    currentTheme,
    handleNodeClick,
    handleZoomIn,
    handleZoomOut,
    handleZoomToFit,
    toggleThemeCatalog,
    toggleStyleCatalog,
    toggleClusterCatalog,
    toggleExportCatalog,
    isLinkConnected,
    isLinkOfSelectedType,
    currentContextPayload,
    handleCopy,
    guidance,
  };
}
