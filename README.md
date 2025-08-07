# Valthera

**Valthera** is an open-source system for building your own computer vision stack — including software, hardware, and AI tools.

You can:

* Build a stereo depth camera using our hardware designs
* Run video through a GPU-based processing pipeline
* Use a built-in agent to help train your own video classifiers
* Deploy models to the cloud or on local hardware like Jetson Nano

Everything is open-source. No need for labeled datasets or ML expertise.

---

## What's Included

Valthera comes with:

**1. Software**

* Video processing with V-JEPA embeddings
* LLM-powered agent to help define and train classifiers
* Frontend app to view videos, define concepts, and monitor models
* Backend API and storage using AWS tools (Lambda, S3, DynamoDB)
* Local setup scripts for running everything on your machine

**2. Hardware**

* Open-source stereo vision rig with 3D-printable parts
* Jetson Nano-compatible GPU processing unit
* Camera calibration, wiring, and setup instructions
* Support for USB cameras and live video capture

---

## Use Cases

You can use Valthera to:

* Train a robot to detect when a task is complete
* Monitor lab equipment or track experiment steps
* Watch for safety events in a room or workspace
* Classify movement patterns in video without writing code

---

## How It Works

1. **Upload or stream a video**
2. **Tell the agent** what kind of event or behavior you want to detect
3. **Train a classifier** based on your concept
4. **Deploy the model** and run predictions on new video

The agent helps at every step. You can run this locally or in the cloud.

---

## Project Layout

```
valthera/
├── app/           # Frontend UI
├── agent/         # LangGraph agent
├── lambdas/       # Backend functions
├── containers/    # Video processing
├── devices/       # Camera support (Jetson, RealSense)
├── hardware/      # CAD files, setup guides, diagrams
├── scripts/       # Dev tools and local setup
└── packages/      # Shared Python code
```

---

## Getting Started

```bash
git clone https://github.com/valthera/valthera.git
cd valthera
./valthera-local start
```

This sets up:

* React app at [http://localhost:5173](http://localhost:5173)
* API backend at [http://localhost:3000](http://localhost:3000)
* Local S3, DynamoDB, and Cognito
* Docker containers for V-JEPA and agent

To build the stereo camera, check the `hardware/` folder for CAD files and setup steps.

---

## Want to Help?

We’re looking for people to:

* Improve the video processing pipeline
* Contribute to the LangGraph agent
* Help test and improve the hardware design
* Add new model training tools
* Use Valthera in real robotics or video projects

Start with [CONTRIBUTING.md](./CONTRIBUTING.md) or open an issue with ideas.

---

## License

* Software: Apache 2.0
* Hardware: CERN-OHL-W v2

---

## Summaryg

Valthera gives you the full stack for building custom video classifiers — from the camera to the model. It’s open-source, runs locally or in the cloud, and is designed to be simple to use and easy to modify.