The original concept we mapped out for linking data narratives directly with interactive user behavior is known as **Scrollytelling (Scroll-Driven Choreography)**.

Instead of treating the data visualization and the written report as two separate, isolated side-by-side components, this design weaves them into a single, cohesive cinematic document.

Here is a breakdown of the structural blueprint of that original idea:

### 1. The Screen Division (Fixed vs. Scrolling)

The layout splits the user's viewport into a **60/40 presentation layer**:

* **Left Side (60% Width — The Stage):** The 3D WebGL Canvas stays completely fixed and locked to the screen background. It acts like a camera viewport on a physical space. It never scrolls off the page.
* **Right Side (40% Width — The Narrative Track):** A standard vertical scroll container where the AI-generated stories (the "chapters") live. Each `reassignment_reason` or incident story is designed as a distinct, full-height card (`min-h-screen`).

### 2. Scroll-Linked Synchronization (The Interaction Loop)

As the executive or engineer reads through the report and scrolls down the right-hand panel, an **Intersection Observer hook** tracks which chapter card is currently centered in the viewport.

When a new chapter hits the reading threshold:

1. It reads the metadata tag of that story (e.g., `data-cluster="eSIM not active"`).
2. It broadcasts an immediate spatial instruction to the WebGL canvas.

### 3. Camera Choreography & Visual Focus

The fixed 3D canvas dynamically reacts to the scrolling position in real-time using linear interpolation (`lerp`) to adjust the scene state smoothly:

* **Dynamic Camera Pan & Zoom:** The camera automatically unlocks from the global view, glides through the 3D grid coordinates, and zeroes in tightly on the bounding sphere of the specific territory associated with that chapter.
* **Contextual Focus Dimming:** To eliminate visual noise, points belonging to the active chapter remain fully visible and vibrant, while the surrounding fringe clusters smoothly fade down to a translucent background state (`opacity: 0.05`).
* **Vector Activation:** The local 3D eigenvector arrows and text labels (`Queue: CS`, `Reassigned: IT`) for that cluster smoothly fade into view at the same time to show the exact latent parameters driving that precise incident.

### Why this Model Excels for Mobile Core Analysis

When dealing with complex telemetry like your SSoT file, showing an entire global network cloud at once can trigger cognitive overload. By utilizing this scrollytelling concept, you guide the reader through an organized sequence of operational events—letting them absorb the narrative context while the 3D visual space effortlessly moves to isolate and match the data they are reading.