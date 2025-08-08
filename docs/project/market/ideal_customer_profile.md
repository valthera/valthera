**Valthera Ideal Customer Profile (ICP): Problem-Centric**

**Primary Market**: Early-stage robotics startups (Seed to Series A) building robot arms, humanoids, or industrial automation systems, primarily in tech hubs like SF Bay Area, Boston, or Berlin.

**Customer Segments**:
1. **Robot Arm Startups**: Focused on micro-tasking (e.g., pick-and-place, button pushing, cable routing).
2. **Humanoid & Multi-purpose Platforms**: Experimenting with wrist-mounted cameras and dynamic environments.
3. **Next-Gen Industrial Automation**: Modernizing vision-based control for factories/warehouses.

**Core Problems They’re Solving**:
1. **Lack of Labeled, Real-World Data**:
   - Need datasets for fine motor tasks (e.g., grasping screws, inserting connectors).
   - Current datasets don’t match their unique setups or environments.
   - Manual labeling is slow, costly, and prone to errors.
2. **Cloud-Based Perception Limitations**:
   - Require real-time feedback for robot tasks, but cloud pipelines introduce latency and cost.
   - Need edge-first vision to operate in real-world settings (e.g., factories, homes).
   - Face regulatory/security constraints prohibiting cloud reliance.
3. **Heavy/Bulky Vision Hardware**:
   - Wrist-mounted cameras are often too heavy, disrupting robot balance.
   - Need lightweight, modular vision systems with compute offloaded to the robot body or external devices like Jetson.
4. **Rigid, Expensive Vision Stacks**:
   - Closed systems are costly (e.g., $2k+ dev kits) and slow to iterate.
   - Small teams need affordable (<$500), open-source tools for rapid prototyping and customization.
5. **Time-Intensive Data Infrastructure**:
   - Building tools for data capture, labeling, and replay diverts focus from core robotics development.
   - Need plug-and-play systems with local recording, auto-labeling, and ROS/PyTorch/WebRTC compatibility.

**Buyer Persona**:
- **CTO/Head of Robotics**: Needs a fast-to-deploy, edge-first perception stack that’s ROS/PyTorch compatible.
- **Robotics/ML Engineer**: Struggles with low-latency feedback and real-world data labeling for model training.
- **Hardware Lead**: Requires lightweight, mountable cameras and modular compute to maintain robot balance.

**Key Requirements**:
- Lightweight, wrist-mountable cameras with offboard compute (e.g., Jetson, Xavier).
- Local-first, low-latency vision pipeline (no cloud dependency).
- Open-source, affordable (<$500) system with ROS integration, PyTorch/TensorFlow support, and auto-labeling tools.
- Modular hardware/software for rapid iteration and experimentation.

**Summary**: Valthera’s ICP is an early-stage robotics startup with a small, technical team building robot arms or humanoids for micro-tasks. They need an affordable, open-source, edge-first vision system to overcome challenges with real-world data, heavy cameras, cloud latency, and complex data infrastructure, enabling rapid prototyping and deployment.