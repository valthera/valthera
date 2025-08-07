# Valthera: Language-Guided Video Intelligence

**Valthera** is an open-source platform for building intelligent video classifiers using natural language and advanced computer vision. Describe a concept like "robot completes a task" or "person enters restricted zone," and Valthera guides you through building, training, and deploying a model — using your own video data.

Valthera removes the barriers of labeled datasets, complex infrastructure, and ML expertise. It is cloud-native, GPU-accelerated, and designed for those pushing the frontier of video perception, robotics, and intelligent systems.

## What Valthera Offers

Valthera integrates a full-stack video intelligence pipeline:

- **Video Processing** using V-JEPA embeddings for temporal understanding
- **LLM-Powered Agent** to define visual concepts and automate training
- **Custom Classifier Training** optimized for few-shot learning from real video
- **Open Infrastructure** with AWS Lambda, S3, DynamoDB, and containerized compute
- **Optional RealSense Support** for edge video capture and live feedback

Imagine a robotics engineer training a task detector with a single camera feed and a few natural language prompts. Or a healthcare team deploying a patient-movement model with zero data science support. Valthera enables this — today.

## Why This Matters

Video understanding is one of the most complex and impactful frontiers in AI. But today, most teams are blocked by high labeling costs, infrastructure complexity, and the ML expertise gap.

Valthera closes that gap with an LLM-guided pipeline that brings video intelligence to everyone — researchers, developers, and domain experts — without sacrificing power or flexibility.

## Use Cases

- **Robotics**: Detect task transitions, tool use, or failure conditions from video
- **Lab Automation**: Track experiment protocols, equipment status, or safety compliance
- **Retail**: Analyze customer movement, engagement, or checkout efficiency
- **Healthcare**: Monitor mobility, bed exits, or equipment usage
- **Creative AI**: Classify motion in dance, sport, or performance without manual labels

## Agent Workflow

At the heart of Valthera is a LangGraph-based agent that coordinates model creation:

1. You describe what you want to detect in plain language
2. The agent recommends relevant data, masking, and training strategy
3. It launches training and exposes the model as a usable endpoint
4. You can review model behavior and iterate using natural feedback

This makes concept learning interactive, explainable, and highly adaptable — even for non-technical users.

## Technical Stack

| Layer      | Technology                                 |
|------------|-------------------------------------------|
| Frontend   | React with TypeScript                     |
| Backend    | AWS Lambda via SAM                        |
| Storage    | S3 (video) and DynamoDB (metadata)       |
| Embeddings | V-JEPA video encoder in PyTorch containers |
| Agent      | LangGraph LLM workflows                   |
| Infra      | CDK + Docker + local emulation tools     |

All services are containerized and runnable locally or in production environments.

## Technical Challenges We Are Exploring

We are actively researching and building solutions to these cutting-edge problems:

### Visual Concept Learning

- Modeling temporal context with minimal supervision
- Learning from masked and sparse data in real video
- Aligning natural language with complex visual behavior
- Handling occlusion, motion blur, and domain drift

### Agent Intelligence

- Integrating active learning and error feedback loops
- Prompt engineering for training supervision
- Explaining classifier behavior in human terms
- Automated evaluation and curriculum design

### Scalable Infrastructure

- Streaming inference from live camera feeds
- Real-time deployment on Jetson Nano and Coral TPU
- Auto-scaling training pipelines for large datasets
- Cross-device synchronization and multi-user support

These are research-grade problems with opportunities for publication, real-world impact, and collaborative breakthroughs.

## Getting Started

```bash
git clone https://github.com/valthera/valthera.git
cd valthera
./valthera-local start
```

This spins up:

- Frontend: [http://localhost:5173](http://localhost:5173)
- API Gateway: [http://localhost:3000](http://localhost:3000)
- Local S3, DynamoDB, Cognito
- LangGraph agent backend
- V-JEPA processing container

See [docs/](./docs) for full instructions.

## Project Structure

```
valthera/
├── app/               # React frontend
├── agent/             # LangGraph workflows
├── lambdas/           # Serverless API functions
├── containers/        # Video processing and embedding
├── devices/           # RealSense capture and edge support
├── packages/          # Shared utilities
├── scripts/           # Dev tooling and setup
└── template.yaml      # SAM infrastructure template
```

## Contribute

We are inviting collaborators who want to shape the future of intelligent video systems. If you are interested in:

- Applying few-shot learning to real-world video
- Building agent workflows that reason over visual data
- Designing human-in-the-loop tools for perception
- Deploying scalable pipelines to edge or cloud environments

... then Valthera is an ideal platform.

Start with [CONTRIBUTING.md](./CONTRIBUTING.md) or join a discussion in [Issues](https://github.com/valthera/valthera/issues).

## License

Valthera is open source under the Apache 2.0 license.

## Help Build the Future of Perception

We believe the next frontier in AI is not just about language or images, but physical intelligence — the ability to see, interpret, and respond to the world through video.

Valthera is a foundation for that future.

Join us to explore what's possible when language, vision, and intelligent systems converge — and help build the open infrastructure that powers it.