.PHONY: build run test clean help multiarch jetson

# Default target
help:
	@echo "Available commands:"
	@echo "  make build      - Build the Docker image (single arch)"
	@echo "  make multiarch  - Build multi-architecture image (Mac + Jetson)"
	@echo "  make run        - Run the Docker container (Mac)"
	@echo "  make jetson     - Run the Docker container (Jetson Nano)"
	@echo "  make test       - Test the code locally"
	@echo "  make clean      - Clean up Docker images"
	@echo "  make help       - Show this help message"

# Build the Docker image
build:
	docker build -t camera:latest .

# Run the Docker container
run:
	docker run --rm camera:latest

# Test the code locally (without Docker)
test:
	python test_local.py

# Clean up Docker images
clean:
	docker rmi camera:latest 2>/dev/null || true

# Build multi-architecture image
multiarch:
	docker buildx build --platform linux/amd64,linux/arm64 -t camera:latest .

# Run on Jetson Nano with RealSense
jetson:
	docker run --rm --runtime nvidia --gpus all \
		--privileged -v /dev/bus/usb:/dev/bus/usb \
		camera:latest

# Build and run in one command
build-run: build run

# Interactive shell in container (Mac)
shell:
	docker run -it --rm camera:latest /bin/bash

# Interactive shell in container (Jetson Nano)
shell-jetson:
	docker run -it --rm --runtime nvidia --gpus all \
		--privileged -v /dev/bus/usb:/dev/bus/usb \
		camera:latest /bin/bash 