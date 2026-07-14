"use client";

import React, { useEffect, useRef } from "react";

interface QuantumLogoSwarmProps {
  isLight: boolean;
}

export function QuantumLogoSwarm({ isLight }: QuantumLogoSwarmProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext("webgl") || (canvas.getContext("experimental-webgl") as WebGLRenderingContext | null);
    if (!gl) {
      console.warn("WebGL not supported in this browser.");
      return;
    }

    // Enable blending for transparent particles and keyed texture
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);

    // -------------------------------------------------------------------------
    // 1. Shaders Setup
    // -------------------------------------------------------------------------

    // Shader Source: Particles
    const particleVS = `
      attribute vec3 aPosition;
      attribute vec3 aTarget;
      attribute float aSpeed;
      uniform float uTime;
      uniform float uMorphFactor;
      uniform mediump float uIsLight;
      uniform mat4 uProjection;
      uniform mat4 uModelView;
      uniform vec2 uMouse;
      varying vec3 vColor;
      varying float vDepth;
      varying float vDofBlur;
      
      void main() {
        // Interpolate between initial swarm position and logo target silhouette
        vec3 pos = mix(aPosition, aTarget, uMorphFactor);
        
        // Add a gentle spiral/rotational twist during transition (peaks at morphFactor = 0.5)
        float twistAngle = sin(uMorphFactor * 3.14159265) * 0.7;
        float cosA = cos(twistAngle);
        float sinA = sin(twistAngle);
        float rx = pos.x * cosA - pos.z * sinA;
        float rz = pos.x * sinA + pos.z * cosA;
        pos.x = rx;
        pos.z = rz;
        
        // Turbulence noise (decays when morphing into logo, swells in swarm mode)
        float noiseScale = (1.0 - uMorphFactor) * 0.15 + 0.015;
        pos.x += sin(uTime * 1.5 + aPosition.z) * noiseScale;
        pos.y += cos(uTime * 1.2 + aPosition.x) * noiseScale;
        pos.z += sin(uTime * 1.8 + aPosition.y) * noiseScale;
        
        // Mouse repulsion (decays slightly when logo is fully formed to protect legibility)
        vec4 screenPos = uProjection * uModelView * vec4(pos, 1.0);
        vec2 ndcPos = screenPos.xy / screenPos.w;
        float dist = distance(ndcPos, uMouse);
        if (dist < 0.4) {
          float force = (0.4 - dist) * 0.4 * (1.0 - uMorphFactor * 0.7);
          pos.xy += normalize(ndcPos - uMouse) * force;
        }

        vec4 eyePos = uModelView * vec4(pos, 1.0);
        gl_Position = uProjection * eyePos;
        
        // Depth-of-Field (DoF) calculation
        float distToFocus = abs(eyePos.z - (-2.2)); // Center of the cube is at z = -2.2
        float blurFactor = clamp(distToFocus / 0.7, 0.0, 1.0); // 0.0 at center, 1.0 at front/back faces
        vDofBlur = blurFactor;

        // Scale point size: in-focus particles are smaller/sharper, out-of-focus particles are larger/bokeh-like
        float baseSize = mix(3.5, 7.5, blurFactor);
        gl_PointSize = (baseSize / gl_Position.w) * (sin(uTime * 2.0 + aPosition.y * 10.0) * 0.25 + 1.15) * (0.85 + 0.15 * aSpeed);
        
        // Normalize depth between 0.0 (back, z = -2.9) and 1.0 (front, z = -1.5)
        vDepth = clamp((eyePos.z - (-2.9)) / 1.4, 0.0, 1.0);
        
        // Color gradient: vibrant blue and vibrant purple, darkened in light mode for contrast
        vec3 colorBlue = mix(vec3(0.0, 0.45, 1.0), vec3(0.0, 0.25, 0.75), uIsLight);
        vec3 colorPurple = mix(vec3(0.65, 0.15, 0.95), vec3(0.45, 0.08, 0.72), uIsLight);
        // Mix blue and purple particles dynamically based on position to create a sparkling swarm
        float particleMix = clamp(uMorphFactor + sin(aPosition.x * 12.0) * 0.35, 0.0, 1.0);
        vColor = mix(colorBlue, colorPurple, particleMix);
      }
    `;

    const particleFS = `
      precision mediump float;
      varying vec3 vColor;
      varying float vDepth;
      varying float vDofBlur;
      uniform mediump float uIsLight;
      void main() {
        vec2 temp = gl_PointCoord - vec2(0.5);
        float dist = dot(temp, temp);
        if (dist > 0.25) discard;
        
        // Fuzzy edges for bokeh simulation: sharpness decreases as blur increases
        float r2 = dist * 4.0; // 0.0 to 1.0
        float edgeWidth = mix(0.15, 0.95, vDofBlur);
        float alpha = clamp((1.0 - r2) / edgeWidth, 0.0, 1.0);
        
        // Out-of-focus particles fade out to mimic light dispersion
        float opacityScale = mix(0.95, 0.35, vDofBlur);
        
        // Apply depth-based opacity attenuation (fog) to reveal 3D volume
        // Boost baseline opacity on light background to increase particle contrast
        float baseAlpha = mix(0.85, 0.95, uIsLight);
        float minFog = mix(0.18, 0.35, uIsLight);
        float depthFog = mix(minFog, 1.0, vDepth);
        gl_FragColor = vec4(vColor, alpha * baseAlpha * depthFog * opacityScale);
      }
    `;

    // Shader Source: Wireframe Cube
    const cubeVS = `
      attribute vec3 aPosition;
      uniform mat4 uProjection;
      uniform mat4 uModelView;
      void main() {
        gl_Position = uProjection * uModelView * vec4(aPosition, 1.0);
      }
    `;

    const cubeFS = `
      precision mediump float;
      uniform vec3 uColor;
      uniform float uAlpha;
      void main() {
        gl_FragColor = vec4(uColor, uAlpha);
      }
    `;

    // Shader Source: Logo Plane
    const logoVS = `
      attribute vec3 aPosition;
      attribute vec2 aTexCoord;
      uniform mat4 uProjection;
      uniform mat4 uModelView;
      varying vec2 vTexCoord;
      void main() {
        gl_Position = uProjection * uModelView * vec4(aPosition, 1.0);
        vTexCoord = aTexCoord;
      }
    `;

    const logoFS = `
      precision mediump float;
      uniform sampler2D uTexture;
      uniform float uTime;
      uniform float uOpacity;
      varying vec2 vTexCoord;
      void main() {
        vec4 color = texture2D(uTexture, vTexCoord);
        
        // Key out white background (color components close to 1.0)
        if (color.r > 0.88 && color.g > 0.88 && color.b > 0.88) {
          discard;
        }
        
        // Holographic vertical scanline effect
        float scanline = sin(vTexCoord.y * 60.0 + uTime * 4.0) * 0.06 + 0.94;
        vec3 holoColor = color.rgb * scanline;
        
        gl_FragColor = vec4(holoColor, uOpacity * 0.95);
      }
    `;

    // Helper to compile and link shader program
    const createProgram = (vsSource: string, fsSource: string): WebGLProgram | null => {
      const vs = gl.createShader(gl.VERTEX_SHADER);
      const fs = gl.createShader(gl.FRAGMENT_SHADER);
      if (!vs || !fs) return null;

      gl.shaderSource(vs, vsSource);
      gl.compileShader(vs);
      if (!gl.getShaderParameter(vs, gl.COMPILE_STATUS)) {
        console.error("VS compilation error:", gl.getShaderInfoLog(vs));
        return null;
      }

      gl.shaderSource(fs, fsSource);
      gl.compileShader(fs);
      if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
        console.error("FS compilation error:", gl.getShaderInfoLog(fs));
        return null;
      }

      const program = gl.createProgram();
      if (!program) return null;

      gl.attachShader(program, vs);
      gl.attachShader(program, fs);
      gl.linkProgram(program);
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        console.error("Program link error:", gl.getProgramInfoLog(program));
        return null;
      }
      return program;
    };

    const particleProg = createProgram(particleVS, particleFS);
    const cubeProg = createProgram(cubeVS, cubeFS);
    const logoProg = createProgram(logoVS, logoFS);

    if (!particleProg || !cubeProg || !logoProg) return;

    // -------------------------------------------------------------------------
    // 2. Geometry Buffers
    // -------------------------------------------------------------------------

    // A. Particles data (8000 items)
    const particleCount = 8000;
    const startPositions: number[] = [];
    const targetPositions: number[] = [];
    const speeds: number[] = [];

    for (let i = 0; i < particleCount; i++) {
      // Starting positions (solid sphere swarm with uniform volume distribution)
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      const r = Math.pow(Math.random(), 1.0 / 3.0) * 0.82; // Cubic-root distribution for uniform density in 3D volume
      startPositions.push(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi)
      );

      // Default target positions (fall back to cube layout inside a box)
      targetPositions.push(
        (Math.random() * 2 - 1) * 0.55,
        (Math.random() * 2 - 1) * 0.55,
        (Math.random() * 2 - 1) * 0.55
      );

      speeds.push(0.5 + Math.random() * 1.5);
    }

    const posBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(startPositions), gl.STATIC_DRAW);

    const targetBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, targetBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(targetPositions), gl.STATIC_DRAW);

    const speedBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, speedBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(speeds), gl.STATIC_DRAW);

    // B. Wireframe Cube vertices (12 lines / 24 vertices)
    const s = 0.7; // Half-size
    const cubeVertices = new Float32Array([
      // Top face
      -s,  s, -s,   s,  s, -s,
       s,  s, -s,   s,  s,  s,
       s,  s,  s,  -s,  s,  s,
      -s,  s,  s,  -s,  s, -s,
      // Bottom face
      -s, -s, -s,   s, -s, -s,
       s, -s, -s,   s, -s,  s,
       s, -s,  s,  -s, -s,  s,
      -s, -s,  s,  -s, -s, -s,
      // Vertical pillars
      -s,  s, -s,  -s, -s, -s,
       s,  s, -s,   s, -s, -s,
       s,  s,  s,   s, -s,  s,
      -s,  s,  s,  -s, -s,  s,
    ]);

    const cubeBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, cubeBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, cubeVertices, gl.STATIC_DRAW);

    // B2. Cube Face vertices (6 faces * 2 triangles * 3 vertices = 36 vertices)
    const faceVertices = new Float32Array([
      // Front face (z = s)
      -s, -s,  s,   s, -s,  s,  -s,  s,  s,
      -s,  s,  s,   s, -s,  s,   s,  s,  s,
      // Back face (z = -s)
      -s, -s, -s,  -s,  s, -s,   s, -s, -s,
       s, -s, -s,  -s,  s, -s,   s,  s, -s,
      // Top face (y = s)
      -s,  s, -s,  -s,  s,  s,   s,  s, -s,
       s,  s, -s,  -s,  s,  s,   s,  s,  s,
      // Bottom face (y = -s)
      -s, -s, -s,   s, -s, -s,  -s, -s,  s,
       s, -s,  s,  -s, -s,  s,   s, -s, -s,
      // Right face (x = s)
       s, -s, -s,   s,  s, -s,   s, -s,  s,
       s,  s,  s,   s, -s,  s,   s,  s, -s,
      // Left face (x = -s)
      -s, -s, -s,  -s, -s,  s,  -s,  s, -s,
      -s,  s,  s,  -s,  s, -s,  -s, -s,  s,
    ]);

    const faceBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, faceBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, faceVertices, gl.STATIC_DRAW);

    // C. Logo Plane vertices & texture coordinates
    const w = 0.45; // half-width
    const logoVertices = new Float32Array([
      -w, -w, 0.05,
       w, -w, 0.05,
      -w,  w, 0.05,
       w,  w, 0.05,
    ]);

    const texCoords = new Float32Array([
      0.0, 1.0,
      1.0, 1.0,
      0.0, 0.0,
      1.0, 0.0,
    ]);

    const logoVertexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, logoVertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, logoVertices, gl.STATIC_DRAW);

    const logoTexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, logoTexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, texCoords, gl.STATIC_DRAW);

    // -------------------------------------------------------------------------
    // 3. Texture Loading and Pixel Silhouette Extraction
    // -------------------------------------------------------------------------
    const texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);

    // Placeholder black texture while loading
    gl.texImage2D(
      gl.TEXTURE_2D,
      0,
      gl.RGBA,
      1,
      1,
      0,
      gl.RGBA,
      gl.UNSIGNED_BYTE,
      new Uint8Array([0, 0, 0, 0])
    );

    const image = new Image();
    image.src = "/logo.jpg";
    image.onload = () => {
      // A. Upload WebGL texture
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);

      // B. Analyze image pixels to isolate logo silhouette points
      try {
        const w = image.width || 447;
        const h = image.height || 447;
        const offCanvas = document.createElement("canvas");
        offCanvas.width = w;
        offCanvas.height = h;
        const offCtx = offCanvas.getContext("2d");
        if (offCtx) {
          offCtx.drawImage(image, 0, 0, w, h);
          const imgData = offCtx.getImageData(0, 0, w, h);
          const pixels = imgData.data;

          const silhouettePoints: { x: number; y: number }[] = [];
          for (let y = 0; y < h; y++) {
            for (let x = 0; x < w; x++) {
              const idx = (y * w + x) * 4;
              const r = pixels[idx];
              const g = pixels[idx + 1];
              const b = pixels[idx + 2];

              // Non-white pixel threshold
              if (r < 220 || g < 220 || b < 220) {
                // Map pixel coordinates to WebGL bounds (-0.45 to 0.45)
                silhouettePoints.push({
                  x: ((x / w) * 2 - 1) * 0.45,
                  y: -((y / h) * 2 - 1) * 0.45 // Y-flipped for WebGL space
                });
              }
            }
          }

          if (silhouettePoints.length > 0) {
            const logoTargets = new Float32Array(particleCount * 3);
            for (let i = 0; i < particleCount; i++) {
              // Pick a random point from the logo silhouette coordinates
              const pt = silhouettePoints[Math.floor(Math.random() * silhouettePoints.length)];
              // Jitter slightly to distribute particles volume in Z and prevent exact overlaps
              const jitterX = (Math.random() - 0.5) * 0.015;
              const jitterY = (Math.random() - 0.5) * 0.015;
              const jitterZ = (Math.random() - 0.5) * 0.05; // Thin volume in 3D

              logoTargets[i * 3] = pt.x + jitterX;
              logoTargets[i * 3 + 1] = pt.y + jitterY;
              logoTargets[i * 3 + 2] = jitterZ;
            }

            // Update WebGL target position buffer with the actual logo coordinates
            gl.bindBuffer(gl.ARRAY_BUFFER, targetBuffer);
            gl.bufferData(gl.ARRAY_BUFFER, logoTargets, gl.STATIC_DRAW);
          }
        }
      } catch (err) {
        console.error("Failed to extract logo silhouette:", err);
      }
    };

    // -------------------------------------------------------------------------
    // 4. Matrix Math & State
    // -------------------------------------------------------------------------
    const aspect = 1.0;
    const fov = 45;
    const near = 0.1;
    const far = 10.0;
    
    // Perspective matrix
    const f = 1.0 / Math.tan((fov * Math.PI) / 360);
    const rangeInv = 1.0 / (near - far);
    const projMatrix = new Float32Array([
      f / aspect, 0, 0, 0,
      0, f, 0, 0,
      0, 0, (near + far) * rangeInv, -1,
      0, 0, 2.0 * near * far * rangeInv, 0
    ]);

    const mousePos = { x: 99.0, y: 99.0 };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      mousePos.x = x;
      mousePos.y = y;
    };

    const handleMouseLeave = () => {
      mousePos.x = 99.0;
      mousePos.y = 99.0;
    };

    canvas.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseleave", handleMouseLeave);

    let animationId = 0;
    const startTime = Date.now();

    // -------------------------------------------------------------------------
    // 5. Render Loop
    // -------------------------------------------------------------------------
    const render = () => {
      const uTime = (Date.now() - startTime) / 1000.0;

      // Adjust viewport size dynamically based on bounding client rect to support CSS scale transforms
      const rect = canvas.getBoundingClientRect();
      const rectWidth = Math.round(rect.width) || 96;
      const rectHeight = Math.round(rect.height) || 96;

      if (canvas.width !== rectWidth || canvas.height !== rectHeight) {
        canvas.width = rectWidth;
        canvas.height = rectHeight;
        gl.viewport(0, 0, canvas.width, canvas.height);

        // Update projection matrix values to reflect correct aspect ratio and prevent squeezing
        const currentAspect = 1.0;
        const currentF = 1.0 / Math.tan((fov * Math.PI) / 360);
        const currentRangeInv = 1.0 / (near - far);
        projMatrix[0] = currentF / currentAspect;
        projMatrix[5] = currentF;
        projMatrix[10] = (near + far) * currentRangeInv;
        projMatrix[11] = -1;
        projMatrix[14] = 2.0 * near * far * currentRangeInv;
        projMatrix[15] = 0;
      }

      gl.clearColor(0.0, 0.0, 0.0, 0.0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      // Calculate Morph Factor & Rotation Angle (10-second rotation-aware cycle)
      // - 0s to 2s: Solid Logo Facing Front (Static) [morphFactor = 1.0, theta = 0.0]
      // - 2s to 4s: Speeding Up Rotation + Morphing to Swarm [morphFactor: 1.0 -> 0.0, theta: 0.0 -> 4 * Math.PI]
      // - 4s to 6s: Slow Rotation as Quantum Swarm [morphFactor = 0.0, theta: 4 * Math.PI -> 6 * Math.PI]
      // - 6s to 8s: Speeding Up Rotation + Collapsing to Logo [morphFactor: 0.0 -> 1.0, theta: 6 * Math.PI -> 10 * Math.PI]
      // - 8s to 10s: Solid Logo Facing Front (Static) [morphFactor = 1.0, theta = 10 * Math.PI]
      const cycle = uTime % 10.0;
      let morphFactor = 1.0;
      let theta = 0.0;

      if (cycle < 2.0) {
        morphFactor = 1.0;
        theta = 0.0;
      } else if (cycle < 4.0) {
        const t = (cycle - 2.0) / 2.0; // 0.0 to 1.0
        const ease = t * t * (3.0 - 2.0 * t); // smoothstep
        morphFactor = 1.0 - ease;
        theta = ease * (4.0 * Math.PI); // 2 full spins (720 deg)
      } else if (cycle < 6.0) {
        morphFactor = 0.0;
        theta = 4.0 * Math.PI; // No rotation for the swarm (stays static at 4*PI)
      } else if (cycle < 8.0) {
        const t = (cycle - 6.0) / 2.0; // 0.0 to 1.0
        const ease = t * t * (3.0 - 2.0 * t); // smoothstep
        morphFactor = ease;
        theta = (4.0 * Math.PI) + ease * (4.0 * Math.PI); // 2 full spins (720 deg, ends at 8*PI)
      } else {
        morphFactor = 1.0;
        theta = 8.0 * Math.PI; // Stop facing front (multiple of 2*PI)
      }

      // Model-View Matrix (No X-axis tilt rotation to keep the logo exactly front-facing wall straight)
      const cY = Math.cos(theta);
      const sY = Math.sin(theta);

      const modelViewMatrix = new Float32Array([
        cY,          0,   -sY,         0,
        0,           1,   0,           0,
        sY,          0,   cY,          0,
        0,           0,   -1.65,       1
      ]);

      // Disable depth writing during transparent/translucent passes to prevent self-clipping artifacts
      gl.depthMask(false);

      // --- Draw Translucent Cube Faces ---
      // gl.useProgram(cubeProg);
      // const cubeProjLoc = gl.getUniformLocation(cubeProg, "uProjection");
      // const cubeMvLoc = gl.getUniformLocation(cubeProg, "uModelView");
      // const cubeColorLoc = gl.getUniformLocation(cubeProg, "uColor");
      // const cubeAlphaLoc = gl.getUniformLocation(cubeProg, "uAlpha");

      // gl.uniformMatrix4fv(cubeProjLoc, false, projMatrix);
      // gl.uniformMatrix4fv(cubeMvLoc, false, modelViewMatrix);
      // gl.uniform3fv(
      //   cubeColorLoc, 
      //   isLight ? new Float32Array([0.05, 0.6, 0.9]) : new Float32Array([0.0, 0.9, 1.0])
      // );
      // gl.uniform1f(cubeAlphaLoc, isLight ? 0.16 : 0.22);

      // const cubePosAttrib = gl.getAttribLocation(cubeProg, "aPosition");
      // gl.enableVertexAttribArray(cubePosAttrib);
      // gl.bindBuffer(gl.ARRAY_BUFFER, faceBuffer);
      // gl.vertexAttribPointer(cubePosAttrib, 3, gl.FLOAT, false, 0, 0);

      // gl.drawArrays(gl.TRIANGLES, 0, 36);

      // --- Draw Wireframe 3D Cube Lines ---
      // gl.uniform1f(cubeAlphaLoc, isLight ? 0.50 : 0.42);
      // gl.bindBuffer(gl.ARRAY_BUFFER, cubeBuffer);
      // gl.vertexAttribPointer(cubePosAttrib, 3, gl.FLOAT, false, 0, 0);

      // gl.drawArrays(gl.LINES, 0, 24);

      // Re-enable depth writing for the logo plane so it correctly occludes particles behind it
      gl.depthMask(true);

      // --- Draw Holographic Logo Plane ---
      gl.useProgram(logoProg);
      const logoProjLoc = gl.getUniformLocation(logoProg, "uProjection");
      const logoMvLoc = gl.getUniformLocation(logoProg, "uModelView");
      const logoTimeLoc = gl.getUniformLocation(logoProg, "uTime");
      const logoOpacityLoc = gl.getUniformLocation(logoProg, "uOpacity");
      const logoSamplerLoc = gl.getUniformLocation(logoProg, "uTexture");

      gl.uniformMatrix4fv(logoProjLoc, false, projMatrix);
      gl.uniformMatrix4fv(logoMvLoc, false, modelViewMatrix);
      gl.uniform1f(logoTimeLoc, uTime);
      gl.uniform1f(logoOpacityLoc, Math.pow(morphFactor, 3.0)); // Fade image in sync with morphing particles (non-linear for clean look)

      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, texture);
      gl.uniform1i(logoSamplerLoc, 0);

      const logoPosAttrib = gl.getAttribLocation(logoProg, "aPosition");
      gl.enableVertexAttribArray(logoPosAttrib);
      gl.bindBuffer(gl.ARRAY_BUFFER, logoVertexBuffer);
      gl.vertexAttribPointer(logoPosAttrib, 3, gl.FLOAT, false, 0, 0);

      const logoTexAttrib = gl.getAttribLocation(logoProg, "aTexCoord");
      gl.enableVertexAttribArray(logoTexAttrib);
      gl.bindBuffer(gl.ARRAY_BUFFER, logoTexBuffer);
      gl.vertexAttribPointer(logoTexAttrib, 2, gl.FLOAT, false, 0, 0);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

      // Disable depth writing again for the particles to allow nice additive blending
      gl.depthMask(false);

      // --- Draw Quantum Particle Swarm ---
      gl.useProgram(particleProg);
      const pProjLoc = gl.getUniformLocation(particleProg, "uProjection");
      const pMvLoc = gl.getUniformLocation(particleProg, "uModelView");
      const pTimeLoc = gl.getUniformLocation(particleProg, "uTime");
      const pMorphLoc = gl.getUniformLocation(particleProg, "uMorphFactor");
      const pMouseLoc = gl.getUniformLocation(particleProg, "uMouse");
      const pIsLightLoc = gl.getUniformLocation(particleProg, "uIsLight");

      gl.uniformMatrix4fv(pProjLoc, false, projMatrix);
      gl.uniformMatrix4fv(pMvLoc, false, modelViewMatrix);
      gl.uniform1f(pTimeLoc, uTime);
      gl.uniform1f(pMorphLoc, morphFactor);
      gl.uniform2f(pMouseLoc, mousePos.x, mousePos.y);
      gl.uniform1f(pIsLightLoc, isLight ? 1.0 : 0.0);

      const pPosAttrib = gl.getAttribLocation(particleProg, "aPosition");
      gl.enableVertexAttribArray(pPosAttrib);
      gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
      gl.vertexAttribPointer(pPosAttrib, 3, gl.FLOAT, false, 0, 0);

      const pTargetAttrib = gl.getAttribLocation(particleProg, "aTarget");
      gl.enableVertexAttribArray(pTargetAttrib);
      gl.bindBuffer(gl.ARRAY_BUFFER, targetBuffer);
      gl.vertexAttribPointer(pTargetAttrib, 3, gl.FLOAT, false, 0, 0);

      const pSpeedAttrib = gl.getAttribLocation(particleProg, "aSpeed");
      gl.enableVertexAttribArray(pSpeedAttrib);
      gl.bindBuffer(gl.ARRAY_BUFFER, speedBuffer);
      gl.vertexAttribPointer(pSpeedAttrib, 1, gl.FLOAT, false, 0, 0);

      gl.drawArrays(gl.POINTS, 0, particleCount);

      // Re-enable depth writing
      gl.depthMask(true);

      animationId = requestAnimationFrame(render);
    };

    render();

    // Cleanup WebGL resources
    return () => {
      cancelAnimationFrame(animationId);
      canvas.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("mouseleave", handleMouseLeave);
      gl.deleteBuffer(posBuffer);
      gl.deleteBuffer(targetBuffer);
      gl.deleteBuffer(speedBuffer);
      gl.deleteBuffer(cubeBuffer);
      gl.deleteBuffer(faceBuffer);
      gl.deleteBuffer(logoVertexBuffer);
      gl.deleteBuffer(logoTexBuffer);
      gl.deleteTexture(texture);
    };
  }, [isLight]);

  return (
    <canvas 
      ref={canvasRef} 
      className="w-full h-full block cursor-crosshair"
      style={{ background: "transparent", transform: "translate3d(0, 0, 0)", backfaceVisibility: "hidden" }}
    />
  );
}
