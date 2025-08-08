## Robot arm and humanoid developers need modular, lightweight vision systems to collect and learn from micro task data — without relying on cloud processing

### What problem are they solving?

* Training robots to perform **micro tasks**, such as:
  * Pick up a screw
  * Insert a connector
  * Push a button
  * Sort parts or tools
* These tasks require large amounts of **labeled, fine-grained real-world data**
* Most teams lack the tools to **capture**, **label**, and **learn** from this data **at the edge**


### Why current solutions fall short

| Constraint                       | Impact on micro task learning                                           |
| -------------------------------- | ----------------------------------------------------------------------- |
| **Cameras are too heavy**        | Can’t mount on the **robot arm wrist** without affecting movement       |
| **All-in-one systems**           | No way to separate camera and compute for balance and flexibility       |
| **Cloud-based processing**       | Adds latency, cost, and limits real-world deployment                    |
| **On-device models are complex** | Real-time inference is hard to train, deploy, and maintain              |
| **No integrated data tools**     | Difficult to label, store, and iterate on task data                     |
| **High cost**                    | Puts complete systems out of reach for indie developers and small teams |

### What they actually need

* A **lightweight camera** that can be mounted on the **robot arm wrist**
* **Modular compute** (e.g. Jetson-class) placed near the center of mass or offboard
* **On-device video + inference** for low-latency feedback and labeling
* A **local-first** system with no dependency on the cloud
* Seamless integration with **labeling tools, ROS, PyTorch, and WebRTC**
* A price point of **\$250–\$500** to remain accessible to small teams and indie developers


### Research actions

Investigate how current builders are designing robot arms and vision systems. Potential early customers include:

* [Almond Bot](https://almondbot.com/)
* [K-Scale](https://www.kscale.dev/)