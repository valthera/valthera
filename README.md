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

# Start backend services (Docker containers, SAM API, etc.)
./valthera-local start

# In a new terminal, start the React app
cd app && pnpm run dev
```

This sets up:

* **Backend Services** (started by `valthera-local start`):
  * API backend at [http://localhost:3000](http://localhost:3000)
  * Local S3, DynamoDB, and Cognito
  * Docker containers for V-JEPA and agent

* **Frontend App** (started manually):
  * React app at [http://localhost:5173](http://localhost:5173)

### First Time Setup

If this is your first time running the project:

1. **Start backend services:**
   ```bash
   ./valthera-local start
   ```
   This will:
   - Start all Docker containers
   - Set up AWS resources (DynamoDB tables, S3 buckets, SQS queues)
   - Configure Cognito with test user
   - Start SAM API
   - Generate environment files if missing

2. **Start React app:**
   ```bash
   cd app && pnpm run dev
   ```
   This will:
   - Install dependencies if needed
   - Start Vite development server
   - Serve the React app

### Test Credentials

After setup, you can log in with:
- **Email**: test@valthera.com
- **Password**: TestPass123!

### Troubleshooting

If you encounter issues:

- **Check service status:** `./valthera-local status`
- **View logs:** `tail -f logs/sam.log` (backend) or check browser console (frontend)
- **Restart services:** `./valthera-local restart`
- **Port conflicts:** `./valthera-local check-ports`

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