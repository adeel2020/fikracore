"use client";

import { useEffect, useRef } from "react";

/*
 * Animated WebGL plasma background adapted from APEX-UI's ShaderBackground.jsx.
 * The original shader background credits 21st.dev community components and is
 * MIT-licensed. Preserve this attribution when moving or modifying the file.
 */

const vertexShader = `
  attribute vec4 aVertexPosition;
  void main() {
    gl_Position = aVertexPosition;
  }
`;

const fragmentShader = `
  precision highp float;
  uniform vec2 iResolution;
  uniform float iFlow;
  uniform float iVoiceIntensity;
  uniform float iGold;

  const float overallSpeed = 0.08;
  const float gridSmoothWidth = 0.015;
  const float lineFrequency = 0.14;
  const float warpFrequency = 0.4;
  const float warpAmplitude = 1.6;
  const float offsetFrequency = 0.45;
  const float minLineWidth = 0.012;
  const float maxLineWidth = 0.16;
  const int linesPerGroup = 10;

  #define drawCircle(pos, radius, coord) smoothstep(radius + gridSmoothWidth, radius, length(coord - (pos)))
  #define drawSmoothLine(pos, halfWidth, t) smoothstep(halfWidth, 0.0, abs(pos - (t)))

  float random(float t) {
    return (cos(t) + cos(t * 1.3 + 1.3) + cos(t * 1.4 + 1.4)) / 3.0;
  }

  float getPlasmaY(float x, float horizontalFade, float offset, float amp) {
    return random(x * lineFrequency + iFlow * overallSpeed) * horizontalFade * amp + offset;
  }

  void main() {
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 uv = fragCoord.xy / iResolution.xy;
    vec2 space = (fragCoord - iResolution.xy / 2.0) / iResolution.x * 10.0;

    float voiceBoost = iVoiceIntensity;
    float horizontalFade = 1.0 - (cos(uv.x * 6.28) * 0.5 + 0.5);
    float verticalFade = 1.0 - (cos(uv.y * 6.28) * 0.5 + 0.5);

    // Original fluid plasma curvature
    space.y += random(space.x * warpFrequency + iFlow * overallSpeed * 0.3) * warpAmplitude * (0.5 + horizontalFade);
    space.x += random(space.y * warpFrequency + iFlow * overallSpeed * 0.3 + 2.0) * warpAmplitude * horizontalFade;

    vec2 centerUv = uv - vec2(0.5, 0.48);
    float centerDist = length(centerUv * vec2(1.0, iResolution.x / iResolution.y));
    float edgeGlow = smoothstep(0.15, 0.58, centerDist);

    vec4 cyanBase = vec4(0.0, 0.90, 1.0, 1.0);
    vec4 goldBase = vec4(0.98, 0.68, 0.16, 1.0);
    vec4 lineColorBase = mix(cyanBase, goldBase, iGold);
    vec4 lineColorCool = mix(vec4(0.02, 0.52, 0.85, 1.0), vec4(0.72, 0.42, 0.08, 1.0), iGold);

    vec4 bgCenter = vec4(0.001, 0.004, 0.008, 1.0);
    vec4 bgEdge = mix(vec4(0.002, 0.012, 0.020, 1.0), vec4(0.014, 0.007, 0.002, 1.0), iGold);
    vec4 fragColor = mix(bgCenter, bgEdge, edgeGlow * 0.5);
    fragColor *= verticalFade * 0.92 + 0.08;

    vec4 lines = vec4(0.0);
    float lineAmplitude = 0.62 * (1.0 + voiceBoost * 2.2);
    float offsetSpeed = iFlow * overallSpeed * 1.1;
    for (int l = 0; l < linesPerGroup; l++) {
      float normalizedIdx = float(l) / float(linesPerGroup);
      float offsetPos = float(l) + space.x * offsetFrequency;
      float rand = random(offsetPos + offsetSpeed) * 0.5 + 0.5;
      float halfWidth = mix(minLineWidth, maxLineWidth, rand * horizontalFade) / 2.0;
      float offset = random(offsetPos + offsetSpeed * (1.0 + normalizedIdx)) * mix(0.7, 2.4, horizontalFade);
      float linePos = getPlasmaY(space.x, horizontalFade, offset, lineAmplitude);
      float line = drawSmoothLine(linePos, halfWidth, space.y) / 2.0 + drawSmoothLine(linePos, halfWidth * 0.15, space.y);

      float circleX = mod(float(l) + iFlow * overallSpeed, 25.0) - 12.0;
      vec2 circlePos = vec2(circleX, getPlasmaY(circleX, horizontalFade, offset, lineAmplitude));
      line += drawCircle(circlePos, 0.008, space) * 2.2;

      vec4 lineColor = mix(lineColorCool, lineColorBase, uv.y * 0.4 + normalizedIdx * 0.3);
      lines += line * lineColor * (rand * 1.3 + 0.5);
    }

    fragColor += lines * (1.05 + voiceBoost * 1.8);
    gl_FragColor = fragColor;
  }
`;

function compileShader(gl: WebGLRenderingContext, type: number, source: string) {
  const shader = gl.createShader(type);
  if (!shader) return null;
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.error("[mark-shader] compile error", gl.getShaderInfoLog(shader));
    gl.deleteShader(shader);
    return null;
  }
  return shader;
}

export function MarkShaderBackground({
  opacity = 0.16,
  voiceActive = false,
  gold = false,
  speedMultiplier = 1.0,
}: {
  opacity?: number;
  voiceActive?: boolean;
  gold?: boolean;
  speedMultiplier?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const voiceRef = useRef(0);
  const voiceTargetRef = useRef(0);
  const flowRef = useRef(0);
  const goldRef = useRef(gold ? 1 : 0);
  const goldTargetRef = useRef(gold ? 1 : 0);
  const speedRef = useRef(speedMultiplier);
  const speedTargetRef = useRef(speedMultiplier);

  useEffect(() => {
    speedTargetRef.current = speedMultiplier;
  }, [speedMultiplier]);

  useEffect(() => {
    voiceTargetRef.current = voiceActive ? 1 : 0;
  }, [voiceActive]);

  useEffect(() => {
    goldTargetRef.current = gold ? 1 : 0;
  }, [gold]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const gl = canvas?.getContext("webgl");
    if (!canvas || !gl) return;

    const vs = compileShader(gl, gl.VERTEX_SHADER, vertexShader);
    const fs = compileShader(gl, gl.FRAGMENT_SHADER, fragmentShader);
    if (!vs || !fs) return;

    const program = gl.createProgram();
    if (!program) return;
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error("[mark-shader] link error", gl.getProgramInfoLog(program));
      return;
    }

    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);

    const vertexPosition = gl.getAttribLocation(program, "aVertexPosition");
    const resolution = gl.getUniformLocation(program, "iResolution");
    const flow = gl.getUniformLocation(program, "iFlow");
    const voiceIntensity = gl.getUniformLocation(program, "iVoiceIntensity");
    const goldUniform = gl.getUniformLocation(program, "iGold");

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const nextWidth = Math.max(1, Math.floor((canvas.clientWidth || window.innerWidth) * dpr));
      const nextHeight = Math.max(1, Math.floor((canvas.clientHeight || window.innerHeight) * dpr));
      if (canvas.width !== nextWidth || canvas.height !== nextHeight) {
        canvas.width = nextWidth;
        canvas.height = nextHeight;
        gl.viewport(0, 0, canvas.width, canvas.height);
      }
    };

    let raf = 0;
    let lastFrame = 0;
    const render = (timestamp: number) => {
      if (!lastFrame) lastFrame = timestamp;
      const rawDt = (timestamp - lastFrame) / 1000;
      const dt = Math.min(Math.max(rawDt, 0), 1 / 30);
      lastFrame = timestamp;

      const attack = voiceTargetRef.current > voiceRef.current ? 1.4 : 0.55;
      speedRef.current += (speedTargetRef.current - speedRef.current) * Math.min(dt * 2.2, 1);
      voiceRef.current += (voiceTargetRef.current - voiceRef.current) * Math.min(dt * attack * 3, 1);
      goldRef.current += (goldTargetRef.current - goldRef.current) * Math.min(dt * 2.4, 1);
      flowRef.current += dt * (1 + voiceRef.current * 2.4) * speedRef.current;

      gl.clearColor(0, 0, 0, 1);
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.useProgram(program);
      gl.uniform2f(resolution, canvas.width, canvas.height);
      gl.uniform1f(flow, flowRef.current);
      gl.uniform1f(voiceIntensity, voiceRef.current);
      gl.uniform1f(goldUniform, goldRef.current);
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.vertexAttribPointer(vertexPosition, 2, gl.FLOAT, false, 0, 0);
      gl.enableVertexAttribArray(vertexPosition);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

      raf = requestAnimationFrame(render);
    };

    window.addEventListener("resize", resize);
    resize();
    raf = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      gl.deleteProgram(program);
      if (buffer) gl.deleteBuffer(buffer);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        opacity,
        mixBlendMode: "screen",
        pointerEvents: "none",
      }}
    />
  );
}
