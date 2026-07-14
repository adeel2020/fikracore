import { GraphNode, ThemeConfig } from "../../types/context.types";

export function getQuadBezierPoint(
  t: number,
  p0: { x: number; y: number },
  cp: { x: number; y: number },
  p1: { x: number; y: number }
) {
  const oneMinusT = 1 - t;
  return {
    x: oneMinusT * oneMinusT * p0.x + 2 * oneMinusT * t * cp.x + t * t * p1.x,
    y: oneMinusT * oneMinusT * p0.y + 2 * oneMinusT * t * cp.y + t * t * p1.y,
  };
}

export function createNodeCanvasObject(
  focusedNode: GraphNode | null,
  selectedNodeType: string | null,
  nodeStyle: string,
  currentTheme: ThemeConfig,
  layoutMode: string
) {
  const seedCache = new Map<string, number>();

  return (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    if (node.x === undefined || node.y === undefined || isNaN(node.x) || isNaN(node.y)) {
      return;
    }

    const label = node.label || node.id;
    const type = node.type || "Node";
    const color = currentTheme.nodeColors[type] || "#FFFFFF";
    const isFocused = focusedNode?.id === node.id;
    const isSelectedType = selectedNodeType === null || type === selectedNodeType;

    // Hub Node drawing intercept
    if (node.isHub) {
      const hubRadius = 15;
      const hubColor = currentTheme.nodeColors[node.hubType || ""] || "#FFFFFF";

      ctx.save();
      ctx.shadowBlur = 0;
      ctx.shadowColor = "transparent";

      // Outer colored hub outline
      ctx.beginPath();
      ctx.arc(node.x, node.y, hubRadius, 0, 2 * Math.PI);
      ctx.closePath();

      ctx.fillStyle = currentTheme.isDark
        ? "rgba(20, 28, 45, 0.95)"
        : "rgba(240, 243, 248, 0.95)";
      ctx.fill();

      ctx.strokeStyle = hubColor;
      ctx.lineWidth = isFocused ? 4.0 : 2.5;
      ctx.stroke();

      // Draw centered + or - symbol
      ctx.font = "bold 14px monospace";
      ctx.fillStyle = currentTheme.isDark ? "#FFFFFF" : "#111111";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(node.symbol || "+", node.x, node.y);

      // Draw small label underneath the hub node
      ctx.font = "bold 5.5px system-ui, -apple-system, sans-serif";
      const textY = node.y + hubRadius + 5;
      ctx.strokeStyle = currentTheme.isDark ? "rgba(5, 5, 5, 0.85)" : "rgba(255, 255, 255, 0.95)";
      ctx.lineWidth = 1.2;
      ctx.strokeText(label, node.x, textY);

      ctx.fillStyle = isFocused
        ? currentTheme.isDark
          ? "#FFFFFF"
          : "#111111"
        : currentTheme.labelTextColor;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(label, node.x, textY);

      ctx.restore();
      return;
    }

    // Node Radius
    const radius = 9;

    ctx.save();

    // Reset shadow properties to prevent leaked glow states
    ctx.shadowBlur = 0;
    ctx.shadowColor = "transparent";

    // Dim inactive node types if a type filter is active
    if (!isSelectedType) {
      ctx.globalAlpha = currentTheme.inactiveNodeAlpha;
    }

    // Draw dendritic tree for biological neuron visualization in Synapses mode
    if (layoutMode === "synapses" && !node.isHub) {
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = 0.8;
      ctx.globalAlpha = isSelectedType ? 0.45 : currentTheme.inactiveNodeAlpha * 0.45;

      const seed = seedCache.get(node.id) ?? (() => {
        const calculated = node.id.split("").reduce((acc: number, char: string) => acc + char.charCodeAt(0), 0);
        seedCache.set(node.id, calculated);
        return calculated;
      })();

      const numDendrites = 5;
      for (let i = 0; i < numDendrites; i++) {
        // Distribute dendrite branches around the cell body (soma)
        const angle = (i * 2 * Math.PI) / numDendrites + (seed % 10) * 0.12;

        // Start on node circle boundary
        const startX = node.x + radius * Math.cos(angle);
        const startY = node.y + radius * Math.sin(angle);

        ctx.beginPath();
        ctx.moveTo(startX, startY);

        // Main trunk of dendrite
        const midLen = 7 + (seed % 4);
        const midX = startX + midLen * Math.cos(angle + 0.15 * Math.sin(seed + i));
        const midY = startY + midLen * Math.sin(angle + 0.15 * Math.sin(seed + i));
        ctx.lineTo(midX, midY);

        // First tiny branch tip
        const endLen1 = 5 + (seed % 3);
        const endX1 = midX + endLen1 * Math.cos(angle - 0.25);
        const endY1 = midY + endLen1 * Math.sin(angle - 0.25);
        ctx.lineTo(endX1, endY1);

        // Second tiny branch tip
        ctx.moveTo(midX, midY);
        const endLen2 = 4 + (seed % 3);
        const endX2 = midX + endLen2 * Math.cos(angle + 0.35);
        const endY2 = midY + endLen2 * Math.sin(angle + 0.35);
        ctx.lineTo(endX2, endY2);

        ctx.stroke();
      }
      ctx.restore();
    }

    const drawRoundedRect = (
      c: CanvasRenderingContext2D,
      x: number,
      y: number,
      w: number,
      h: number,
      r: number
    ) => {
      c.beginPath();
      c.moveTo(x + r, y);
      c.lineTo(x + w - r, y);
      c.quadraticCurveTo(x + w, y, x + w, y + r);
      c.lineTo(x + w, y + h - r);
      c.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
      c.lineTo(x + r, y + h);
      c.quadraticCurveTo(x, y + h, x, y + h - r);
      c.lineTo(x, y + r);
      c.quadraticCurveTo(x, y, x + r, y);
      c.closePath();
    };

    if (nodeStyle === "badges") {
      // 1. Neo4j Bloom style Pill Badges (text label rendered directly inside the pill capsule)
      ctx.font = `bold 8px system-ui, -apple-system, sans-serif`;
      const textWidth = ctx.measureText(label).width;
      const padX = 8;
      const badgeW = textWidth + padX * 2;
      const badgeH = 17;
      const badgeX = node.x - badgeW / 2;
      const badgeY = node.y - badgeH / 2;

      drawRoundedRect(ctx, badgeX, badgeY, badgeW, badgeH, 8.5);
      ctx.fillStyle = isFocused
        ? currentTheme.isDark
          ? "rgba(22, 22, 22, 0.95)"
          : "rgba(255, 255, 255, 0.95)"
        : currentTheme.isDark
        ? "rgba(12, 12, 12, 0.85)"
        : "rgba(240, 240, 240, 0.85)";
      ctx.fill();

      ctx.strokeStyle = color;
      ctx.lineWidth = isFocused ? 2.5 : 1.5;
      ctx.stroke();

      ctx.fillStyle = isFocused
        ? currentTheme.isDark
          ? "#FFFFFF"
          : "#111111"
        : currentTheme.isDark
        ? color
        : "rgba(15, 23, 42, 0.95)";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(label, node.x, node.y);
    } else {
      if (nodeStyle === "bubble") {
        // 2. Bubble Style (3D Radial Gradient)
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.closePath();

        const grad = ctx.createRadialGradient(
          node.x - radius / 3,
          node.y - radius / 3,
          radius / 10,
          node.x,
          node.y,
          radius
        );
        grad.addColorStop(0, "rgba(255, 255, 255, 0.95)");
        grad.addColorStop(0.3, color);
        grad.addColorStop(0.85, "rgba(12, 12, 12, 0.3)");
        grad.addColorStop(1, "rgba(0, 0, 0, 0.9)");

        ctx.fillStyle = grad;
        ctx.fill();

        ctx.strokeStyle = color;
        ctx.lineWidth = isFocused ? 2.5 : 1.5;
        ctx.stroke();

        // Tiny glossy specular crescent highlight curve at the top-left
        ctx.beginPath();
        ctx.arc(node.x - 2, node.y - 2, radius - 4, Math.PI * 1.0, Math.PI * 1.5);
        ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
        ctx.lineWidth = 0.8;
        ctx.stroke();
      } else if (nodeStyle === "crystal") {
        // 3. Crystal Style (Hexagonal Glass Facets)
        ctx.beginPath();
        const vertexCount = 6;
        const crystalRadius = radius + 2;
        const vertices: { x: number; y: number }[] = [];
        for (let i = 0; i < vertexCount; i++) {
          const angle = (i * Math.PI) / 3 - Math.PI / 6;
          const vx = node.x + crystalRadius * Math.cos(angle);
          const vy = node.y + crystalRadius * Math.sin(angle);
          vertices.push({ x: vx, y: vy });
          if (i === 0) ctx.moveTo(vx, vy);
          else ctx.lineTo(vx, vy);
        }
        ctx.closePath();

        const glassGrad = ctx.createLinearGradient(
          node.x - crystalRadius,
          node.y - crystalRadius,
          node.x + crystalRadius,
          node.y + crystalRadius
        );
        glassGrad.addColorStop(0, "rgba(255, 255, 255, 0.35)");
        glassGrad.addColorStop(0.4, `${color}44`);
        glassGrad.addColorStop(0.8, "rgba(10, 10, 10, 0.5)");
        glassGrad.addColorStop(1, "rgba(0, 0, 0, 0.95)");

        ctx.fillStyle = glassGrad;
        ctx.fill();

        ctx.strokeStyle = color;
        ctx.lineWidth = isFocused ? 2.5 : 1.5;
        ctx.stroke();

        // Draw internal facet connector lines
        ctx.beginPath();
        vertices.forEach((v) => {
          ctx.moveTo(node.x, node.y);
          ctx.lineTo(v.x, v.y);
        });

        // Inner nested shape (concentric facets)
        for (let i = 0; i < vertexCount; i++) {
          const angle = (i * Math.PI) / 3 - Math.PI / 6;
          const vx = node.x + (radius - 3) * Math.cos(angle);
          const vy = node.y + (radius - 3) * Math.sin(angle);
          if (i === 0) ctx.moveTo(vx, vy);
          else ctx.lineTo(vx, vy);
        }
        ctx.closePath();

        ctx.strokeStyle = `${color}77`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      } else {
        // 4. Shape-based renderers (Classic, Glyphs, and Geometric Geometry)
        if (nodeStyle === "geometry") {
          // Draw category-specific geometric shapes
          ctx.beginPath();
          if (type === "Intent") {
            // Diamond
            ctx.moveTo(node.x, node.y - radius - 2);
            ctx.lineTo(node.x + radius + 2, node.y);
            ctx.lineTo(node.x, node.y + radius + 2);
            ctx.lineTo(node.x - radius - 2, node.y);
            ctx.closePath();
          } else if (type === "Service") {
            // Hexagon
            for (let i = 0; i < 6; i++) {
              const angle = (i * Math.PI) / 3;
              ctx.lineTo(
                node.x + (radius + 2) * Math.cos(angle),
                node.y + (radius + 2) * Math.sin(angle)
              );
            }
            ctx.closePath();
          } else if (type === "Platform") {
            // Square
            ctx.rect(node.x - radius, node.y - radius, radius * 2, radius * 2);
          } else if (type === "Precondition") {
            // Triangle
            ctx.moveTo(node.x, node.y - radius - 2);
            ctx.lineTo(node.x + radius + 2, node.y + radius + 1);
            ctx.lineTo(node.x - radius - 2, node.y + radius + 1);
            ctx.closePath();
          } else if (type === "Error") {
            // Octagon
            for (let i = 0; i < 8; i++) {
              const angle = (i * Math.PI) / 4 + Math.PI / 8;
              ctx.lineTo(
                node.x + (radius + 2) * Math.cos(angle),
                node.y + (radius + 2) * Math.sin(angle)
              );
            }
            ctx.closePath();
          } else {
            // Circle default
            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
          }
        } else {
          // Circle background for Classic and Glyphs styles
          ctx.beginPath();
          ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
          ctx.closePath();
        }

        // Draw background fill
        ctx.fillStyle = isFocused
          ? currentTheme.isDark
            ? "rgba(10, 10, 10, 0.95)"
            : "rgba(255, 255, 255, 0.95)"
          : currentTheme.isDark
          ? "rgba(22, 22, 22, 0.8)"
          : "rgba(255, 255, 255, 0.9)";
        ctx.fill();

        // Draw outline border
        ctx.strokeStyle = color;
        ctx.lineWidth = isFocused ? 2.5 : 1.5;
        ctx.stroke();

        if (nodeStyle === "glyphs") {
          // Render centered Unicode symbol inside circle
          const GLYPH_SYMBOLS: Record<string, string> = {
            Intent: "❓",
            Service: "📶",
            Platform: "⚙️",
            Precondition: "🛡️",
            Error: "⚠️",
            Channel: "📢",
            CustomerProfile: "👤",
            AppType: "📱",
          };
          const glyph = GLYPH_SYMBOLS[type] || "?";
          ctx.font = `10px system-ui, -apple-system, sans-serif`;
          ctx.fillStyle = color;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(glyph, node.x, node.y + 0.5);
        } else {
          // Classic Style inner dot
          ctx.beginPath();
          ctx.arc(node.x, node.y, 3, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
        }
      }

      // Draw label underneath nodes
      ctx.font = `500 5.5px system-ui, -apple-system, sans-serif`;
      const textY = node.y + radius + 5;
      ctx.strokeStyle = currentTheme.isDark ? "rgba(5, 5, 5, 0.85)" : "rgba(255, 255, 255, 0.95)";
      ctx.lineWidth = 1.2;
      ctx.strokeText(label, node.x, textY);

      ctx.fillStyle = isFocused
        ? currentTheme.isDark
          ? "#FFFFFF"
          : "#111111"
        : currentTheme.labelTextColor;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(label, node.x, textY);
    }

    ctx.restore();
  };
}

export function createLinkCanvasObject(
  focusedNode: GraphNode | null,
  selectedNodeType: string | null,
  currentTheme: ThemeConfig,
  layoutMode: string,
  nodes: GraphNode[],
  nodeStyle: string
) {
  // Pre-build O(1) Map lookup for node properties
  const nodeMap = new Map<string, GraphNode>();
  nodes.forEach((n) => nodeMap.set(n.id, n));

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
    const sourceNode = nodeMap.get(sourceId);
    const targetNode = nodeMap.get(targetId);
    return sourceNode?.type === selectedNodeType || targetNode?.type === selectedNodeType;
  };

  return (link: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    // 1. Draw custom biological neural fiber and electrical synapse if in synapses layout mode
    if (layoutMode === "synapses" && !link.isHubLink) {
      let start = link.source;
      let end = link.target;

      if (typeof start === "string") start = nodeMap.get(start) || start;
      if (typeof end === "string") end = nodeMap.get(end) || end;

      if (
        typeof start === "object" &&
        typeof end === "object" &&
        start.x !== undefined &&
        start.y !== undefined &&
        end.x !== undefined &&
        end.y !== undefined
      ) {
        ctx.save();

        const curvature = 0.35;
        const midX = (start.x + end.x) / 2;
        const midY = (start.y + end.y) / 2;
        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        const px = -dy / dist;
        const py = dx / dist;

        const cpX = midX + px * dist * curvature * 0.5;
        const cpY = midY + py * dist * curvature * 0.5;
        const cp = { x: cpX, y: cpY };

        const startColor = currentTheme.nodeColors[start.type] || "#FFFFFF";
        const endColor = currentTheme.nodeColors[end.type] || "#FFFFFF";

        // Node type filter dimming
        const isSelected =
          selectedNodeType === null ||
          start.type === selectedNodeType ||
          end.type === selectedNodeType;

        ctx.globalAlpha = isSelected ? 1.0 : currentTheme.inactiveNodeAlpha;

        const grad = ctx.createLinearGradient(start.x, start.y, end.x, end.y);
        grad.addColorStop(0, startColor);
        grad.addColorStop(1, endColor);

        const isConnected = isLinkConnected(link);

        // Calculate boundaries relative to node shapes
        const rSource = start.isHub ? 15 : nodeStyle === "badges" ? 12 : 9;
        const rTarget = end.isHub ? 15 : nodeStyle === "badges" ? 12 : 9;

        const tStartBound = Math.min(0.4, Math.max(0.01, rSource / dist));
        const tEndBound = Math.max(0.6, Math.min(0.99, 1 - rTarget / dist));

        // Axon hillock at source soma
        const hillockPt = getQuadBezierPoint(tStartBound, start, cp, end);
        const hillockEnd = getQuadBezierPoint(tStartBound + 0.05, start, cp, end);
        const dx_h = hillockEnd.x - hillockPt.x;
        const dy_h = hillockEnd.y - hillockPt.y;
        const len_h = Math.sqrt(dx_h * dx_h + dy_h * dy_h) || 1;
        const nx_h = -dy_h / len_h;
        const ny_h = dx_h / len_h;

        ctx.beginPath();
        ctx.moveTo(hillockPt.x - 3.5 * nx_h, hillockPt.y - 3.5 * ny_h);
        ctx.lineTo(hillockPt.x + 3.5 * nx_h, hillockPt.y + 3.5 * ny_h);
        ctx.lineTo(hillockEnd.x, hillockEnd.y);
        ctx.closePath();
        ctx.fillStyle = startColor;
        ctx.fill();

        const sheathWidth = isConnected ? 9.5 : 6.0;
        const coreWidth = isConnected ? 2.5 : 1.1;

        // Myelin Sheath segments (nodes of Ranvier in between)
        const L = tEndBound - tStartBound;
        const myelinSegments = [
          { s: tStartBound + L * 0.08, e: tStartBound + L * 0.32 },
          { s: tStartBound + L * 0.4, e: tStartBound + L * 0.64 },
          { s: tStartBound + L * 0.72, e: tStartBound + L * 0.92 },
        ];

        myelinSegments.forEach((seg) => {
          ctx.beginPath();
          const steps = 6;
          for (let i = 0; i <= steps; i++) {
            const t = seg.s + (i / steps) * (seg.e - seg.s);
            const pt = getQuadBezierPoint(t, start, cp, end);
            if (i === 0) ctx.moveTo(pt.x, pt.y);
            else ctx.lineTo(pt.x, pt.y);
          }
          ctx.strokeStyle = isConnected ? `${startColor}35` : `${startColor}15`;
          ctx.lineWidth = sheathWidth;
          ctx.lineCap = "round";
          ctx.stroke();
        });

        // Continuous Axon core
        ctx.beginPath();
        const axonSteps = 30;
        for (let i = 0; i <= axonSteps; i++) {
          const t = tStartBound + (i / axonSteps) * (tEndBound - tStartBound);
          const pt = getQuadBezierPoint(t, start, cp, end);
          if (i === 0) ctx.moveTo(pt.x, pt.y);
          else ctx.lineTo(pt.x, pt.y);
        }
        ctx.strokeStyle = grad;
        ctx.lineWidth = coreWidth;
        ctx.lineCap = "round";
        ctx.stroke();

        // Dynamic action potential spark (wiggly electric wave)
        ctx.save();
        ctx.beginPath();
        const waveSteps = 40;
        for (let i = 0; i <= waveSteps; i++) {
          const t = tStartBound + (i / waveSteps) * (tEndBound - tStartBound);
          const basePt = getQuadBezierPoint(t, start, cp, end);

          const tNext = Math.min(tEndBound, t + 0.01);
          const nextPt = getQuadBezierPoint(tNext, start, cp, end);
          const dx_w = nextPt.x - basePt.x;
          const dy_w = nextPt.y - basePt.y;
          const len_w = Math.sqrt(dx_w * dx_w + dy_w * dy_w) || 1;
          const nx_w = -dy_w / len_w;
          const ny_w = dx_w / len_w;

          const timeScale = Date.now() * 0.025;
          const frequency = 45;
          const amplitude = isConnected ? 2.2 : 1.2;
          const wiggle = Math.sin(t * frequency - timeScale) * amplitude;

          const px_wiggle = basePt.x + nx_w * wiggle;
          const py_wiggle = basePt.y + ny_w * wiggle;

          if (i === 0) ctx.moveTo(px_wiggle, py_wiggle);
          else ctx.lineTo(px_wiggle, py_wiggle);
        }
        ctx.strokeStyle = isConnected ? "#FFFFFF" : `${endColor}bb`;
        ctx.lineWidth = isConnected ? 1.0 : 0.6;
        ctx.stroke();
        ctx.restore();

        // Gap Junction (Electrical Synapse) at postsynaptic contact
        const prePt = getQuadBezierPoint(tEndBound - 0.04, start, cp, end);
        const endPt = getQuadBezierPoint(tEndBound, start, cp, end);
        const dx_g = endPt.x - prePt.x;
        const dy_g = endPt.y - prePt.y;
        const len_g = Math.sqrt(dx_g * dx_g + dy_g * dy_g) || 1;
        const nx_g = -dy_g / len_g;
        const ny_g = dx_g / len_g;

        // 1. Presynaptic membrane bouton plate
        ctx.beginPath();
        ctx.moveTo(prePt.x - 3 * nx_g, prePt.y - 3 * ny_g);
        ctx.lineTo(prePt.x + 3 * nx_g, prePt.y + 3 * ny_g);
        ctx.strokeStyle = startColor;
        ctx.lineWidth = 1.8;
        ctx.lineCap = "round";
        ctx.stroke();

        // 2. Postsynaptic membrane receptor plate
        ctx.beginPath();
        ctx.moveTo(endPt.x - 4 * nx_g, endPt.y - 4 * ny_g);
        ctx.lineTo(endPt.x + 4 * nx_g, endPt.y + 4 * ny_g);
        ctx.strokeStyle = endColor;
        ctx.lineWidth = 2.0;
        ctx.lineCap = "round";
        ctx.stroke();

        // 3. Connexons (gap junction channel pores) bridging the gap
        ctx.beginPath();
        ctx.moveTo(prePt.x - 2 * nx_g, prePt.y - 2 * ny_g);
        ctx.lineTo(endPt.x - 2 * nx_g, endPt.y - 2 * ny_g);

        ctx.moveTo(prePt.x, prePt.y);
        ctx.lineTo(endPt.x, endPt.y);

        ctx.moveTo(prePt.x + 2 * nx_g, prePt.y + 2 * ny_g);
        ctx.lineTo(endPt.x + 2 * nx_g, endPt.y + 2 * ny_g);

        ctx.strokeStyle = isConnected ? "#00FF88" : "#CCFF00";
        ctx.lineWidth = 0.8;
        ctx.stroke();

        ctx.restore();
      }
    }

    // 2. Draw link label text
    // Skip drawing labels for irrelevant connections when type is filtered
    if (selectedNodeType && !isLinkOfSelectedType(link)) return;

    // Zoom-Dependent Link Label Occlusion:
    // Hide link labels by default when zoomed out (globalScale < 1.4) unless connected to the focused node
    if (globalScale < 1.4 && !isLinkConnected(link)) return;

    const label = link.label;
    if (!label) return;

    let start = link.source;
    let end = link.target;

    if (typeof start === "string") start = nodeMap.get(start) || start;
    if (typeof end === "string") end = nodeMap.get(end) || end;

    if (typeof start !== "object" || typeof end !== "object") return;
    if (start.x === undefined || start.y === undefined || end.x === undefined || end.y === undefined) return;

    // Calculate midpoint
    const textPos = {
      x: start.x + (end.x - start.x) / 2,
      y: start.y + (end.y - start.y) / 2,
    };

    let relAngle = Math.atan2(end.y - start.y, end.x - start.x);

    // Keep text right-side up (between -90 and 90 degrees)
    if (relAngle > Math.PI / 2) relAngle -= Math.PI;
    if (relAngle < -Math.PI / 2) relAngle += Math.PI;

    ctx.save();
    ctx.translate(textPos.x, textPos.y);
    ctx.rotate(relAngle);

    ctx.font = "bold 6.5px monospace";
    const textWidth = ctx.measureText(label).width;

    ctx.fillStyle = currentTheme.labelTextBackground;
    ctx.strokeStyle = isLinkConnected(link)
      ? currentTheme.nodeColors[focusedNode?.type || ""] ||
        (currentTheme.isDark ? "#FFFFFF" : "#111111")
      : "transparent";
    ctx.lineWidth = 0.5;

    ctx.beginPath();
    ctx.rect(-textWidth / 2 - 3, -4, textWidth + 6, 8);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = isLinkConnected(link)
      ? currentTheme.isDark
        ? "#FFFFFF"
        : "#111111"
      : currentTheme.labelTextColor;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(label, 0, 0);
    ctx.restore();
  };
}
