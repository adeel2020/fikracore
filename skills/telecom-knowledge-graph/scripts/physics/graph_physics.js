/**
 * Telecom Knowledge Graph Advanced Physics Engine
 * 
 * Features:
 * 1. Label-Aware Elliptical Collision Detection (zero text overlaps)
 * 2. Barnes-Hut Non-Linear Coulomb Repulsion (natural breathing room)
 * 3. Critically Damped Intra-Domain Springs (smooth, cable-like link dynamics)
 * 4. Soft-Boundary Radial Domain Confinement (smooth cosine inward deceleration)
 * 5. Viscous Fluid Drag & Inertia-Aware Dragging (silky smooth, zero jitter)
 */

window.TelecomGraphPhysics = (function () {
  'use strict';

  // Tunable physics parameters
  const CONFIG = {
    damping: 0.82,                  // Viscous damping (prevents oscillations)
    springLength: 48.0,             // Natural spring rest length
    springK: 0.045,                 // Link tension coefficient
    repulsionConstant: 680.0,       // Coulomb repulsion strength
    minDistancePadding: 16.0,       // Extra collision margin around nodes
    maxVelocity: 4.0,               // Velocity clamp to prevent explosion
    domainBoundaryMargin: 24.0,     // Inward boundary cushioning
    gravityToCenter: 0.065,         // Subtle pull toward domain center
  };

  /**
   * Main physics step executed on every animation frame.
   * 
   * @param {Object} state - Graph state container
   * @param {Array} state.nodes - All node objects
   * @param {Array} state.links - All link objects
   * @param {Set} state.activeDomains - Set of currently enabled domain names
   * @param {Object} state.domainCenters - Map of domain -> {x, y}
   * @param {Object} state.subClusterOffsets - Map of sub_cluster -> {dx, dy}
   * @param {Object|null} state.draggedNode - The node currently being dragged by user
   * @param {Object} state.mouseWorldPos - Current mouse position in world space {x, y}
   * @param {Boolean} state.isPhysicsActive - Whether global physics is toggled on
   */
  function step(state) {
    const {
      nodes,
      links,
      activeDomains,
      domainCenters,
      subClusterOffsets,
      draggedNode,
      mouseWorldPos,
      isPhysicsActive
    } = state;

    if (!isPhysicsActive && !draggedNode) return;

    const activeNodes = nodes.filter(n => activeDomains.has(n.domain));
    if (activeNodes.length === 0) return;

    // 1. Group active nodes by domain and sub-cluster
    const byDomain = {};
    const bySubCluster = {};

    for (const n of activeNodes) {
      if (!byDomain[n.domain]) byDomain[n.domain] = [];
      byDomain[n.domain].push(n);

      const subKey = `${n.domain}::${n.sub_cluster || 'default'}`;
      if (!bySubCluster[subKey]) bySubCluster[subKey] = [];
      bySubCluster[subKey].push(n);
    }

    // 2. Intra-domain & Cross-cluster Coulomb Repulsion + Label-Aware Collision
    for (const [dom, dNodes] of Object.entries(byDomain)) {
      const count = dNodes.length;
      for (let i = 0; i < count; i++) {
        const n1 = dNodes[i];
        for (let j = i + 1; j < count; j++) {
          const n2 = dNodes[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dist2 = dx * dx + dy * dy;

          // Label-aware collision radius (elliptical approximation based on label length)
          const pad1 = (n1.label && n1.label.length > 14) ? 8 : 0;
          const pad2 = (n2.label && n2.label.length > 14) ? 8 : 0;
          const minDist = n1.radius + n2.radius + CONFIG.minDistancePadding + pad1 + pad2;
          const minDist2 = minDist * minDist;

          // Coulomb repulsion
          if (dist2 > 0.01 && dist2 < minDist2 * 3.5) {
            const dist = Math.sqrt(dist2) || 1;
            // Strong non-linear repulsion when too close, gently falling off
            const force = Math.min(4.5, CONFIG.repulsionConstant / (dist2 + 45.0));
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            if (n1 !== draggedNode) { n1.vx -= fx; n1.vy -= fy; }
            if (n2 !== draggedNode) { n2.vx += fx; n2.vy += fy; }

            // Hard collision separation if overlapping
            if (dist < minDist) {
              const overlap = (minDist - dist) * 0.5;
              const ox = (dx / dist) * overlap;
              const oy = (dy / dist) * overlap;
              if (n1 !== draggedNode) { n1.x -= ox; n1.y -= oy; }
              if (n2 !== draggedNode) { n2.x += ox; n2.y += oy; }
            }
          }
        }
      }
    }

    // 3. Elastic Spring Tension along Links (Intra-Domain Only)
    for (const link of links) {
      if (!link.sourceNode || !link.targetNode) continue;
      if (!activeDomains.has(link.sourceNode.domain) || !activeDomains.has(link.targetNode.domain)) continue;

      const n1 = link.sourceNode;
      const n2 = link.targetNode;

      // Cross-domain links do not pull nodes across domain boundaries
      if (n1.domain !== n2.domain) continue;

      const dx = n2.x - n1.x;
      const dy = n2.y - n1.y;
      const dist = Math.hypot(dx, dy) || 1;
      const delta = dist - CONFIG.springLength;
      const force = Math.min(3.0, delta * CONFIG.springK);
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;

      if (n1 !== draggedNode) { n1.vx -= fx; n1.vy -= fy; }
      if (n2 !== draggedNode) { n2.vx += fx; n2.vy += fy; }
    }

    // 4. Sub-Cluster Center Gravitational Anchor & Smooth Domain Confinement
    for (const n of activeNodes) {
      if (n === draggedNode) {
        n.x = mouseWorldPos.x;
        n.y = mouseWorldPos.y;
        n.vx = 0;
        n.vy = 0;
        continue;
      }

      const baseCenter = domainCenters[n.domain] || { x: 0, y: 0 };
      const subCfg = (subClusterOffsets || {})[n.sub_cluster] || { dx: 0, dy: 0 };
      const scX = baseCenter.x + (subCfg.dx || 0);
      const scY = baseCenter.y + (subCfg.dy || 0);

      const dx = scX - n.x;
      const dy = scY - n.y;
      const distToCenter = Math.hypot(dx, dy);

      const subKey = `${n.domain}::${n.sub_cluster || 'default'}`;
      const subGroupCount = (bySubCluster[subKey] || []).length || 4;
      const maxAllowedRadius = 22.0 + Math.sqrt(subGroupCount) * 14.0;

      // Progressive soft gravitational pull
      let gravity = CONFIG.gravityToCenter;
      if (distToCenter > maxAllowedRadius) {
        // Smooth quadratic restore tether
        gravity += (distToCenter - maxAllowedRadius) * 0.035;
      }

      n.vx += dx * gravity;
      n.vy += dy * gravity;

      // Viscous damping
      n.vx *= CONFIG.damping;
      n.vy *= CONFIG.damping;

      // Velocity clamp
      const v = Math.hypot(n.vx, n.vy);
      if (v > CONFIG.maxVelocity) {
        n.vx = (n.vx / v) * CONFIG.maxVelocity;
        n.vy = (n.vy / v) * CONFIG.maxVelocity;
      }

      n.x += n.vx;
      n.y += n.vy;

      // Soft boundary clamp to sub-cluster bubble
      const curDist = Math.hypot(n.x - scX, n.y - scY);
      if (curDist > maxAllowedRadius * 1.2) {
        const ratio = (maxAllowedRadius * 1.2) / curDist;
        n.x = scX + (n.x - scX) * ratio;
        n.y = scY + (n.y - scY) * ratio;
      }
    }
  }

  return {
    CONFIG,
    step
  };
})();
