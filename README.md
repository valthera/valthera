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

# In a new terminal, install React app dependencies and start the app
cd app && pnpm install && pnpm run dev
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

2. **Install React app dependencies and start the app:**
   ```bash
   cd app && pnpm install && pnpm run dev
   ```
   This will:
   - Install all React app dependencies
   - Start Vite development server
   - Serve the React app

### Subsequent Runs

For subsequent runs, you can skip the install step if dependencies are already installed:

```bash
# Start backend services
./valthera-local start

# Start React app (if dependencies are already installed)
cd app && pnpm run dev
```

### Test Credentials

After setup, you can log in with:
- **Email**: test@valthera.com
- **Password**: TestPass123!

### Monitoring SQS Queues

The local SQS service (ElasticMQ) runs on port 9324. You can monitor queues using these methods:

#### Using AWS CLI
```bash
# List all queues
aws --endpoint-url http://localhost:9324 sqs list-queues | jq

# Check queue message counts
aws --endpoint-url http://localhost:9324 sqs get-queue-attributes \
  --queue-url "http://localhost:9324/123456789012/video-processor-queue" \
  --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible,ApproximateAgeOfOldestMessage
```

#### Using SQS Admin Web UI
The startup script automatically installs `sqs-admin`, which provides a web interface:

```bash
# Start the SQS Admin web interface
sqs-admin --endpoint http://localhost:9324
```

Then open http://localhost:3001 in your browser to view and manage queues.

#### Quick Status Check
```bash
# Watch queue status in real-time
watch -n 2 'aws --endpoint-url http://localhost:9324 sqs list-queues | jq -r ".QueueUrls[]" | while read url; do name=$(basename "$url"); count=$(aws --endpoint-url http://localhost:9324 sqs get-queue-attributes --queue-url "$url" --attribute-names ApproximateNumberOfMessages --query "Attributes.ApproximateNumberOfMessages" --output text); echo "$name: $count messages"; done'
```

### Troubleshooting

If you encounter issues:

- **Check service status:** `./valthera-local status`
- **View logs:** `tail -f logs/sam.log` (backend) or check browser console (frontend)
- **Restart services:** `./valthera-local restart`
- **Port conflicts:** `./valthera-local check-ports`
- **Reinstall React dependencies:** `cd app && pnpm install`

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

## Summary

Valthera gives you the full stack for building custom video classifiers — from the camera to the model. It’s open-source, runs locally or in the cloud, and is designed to be simple to use and easy to modify.