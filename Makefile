# Define all sub-packages
PACKAGES = valthera valthera-langchain valthera-tools

# Default target (run all)
all: install build test

# Install dependencies for all packages
install:
	@for package in $(PACKAGES); do \
		echo "🔧 Installing $$package..."; \
		cd $$package && poetry install && cd ..; \
	done
	@echo "✅ Installation complete!"

# Build all packages
build:
	@for package in $(PACKAGES); do \
		echo "🔨 Building $$package..."; \
		cd $$package && poetry build && cd ..; \
	done
	@echo "✅ Build complete!"

# Install all packages in editable mode
develop:
	@for package in $(PACKAGES); do \
		echo "🔄 Installing $$package in editable mode..."; \
		cd $$package && poetry develop && cd ..; \
	done
	@echo "✅ Development mode set up!"

# Run tests for all packages (if tests/ directory exists)
test:
	@for package in $(PACKAGES); do \
		if [ -d "$$package/tests" ]; then \
			echo "🧪 Running tests for $$package..."; \
			cd $$package && poetry run pytest && cd ..; \
		else \
			echo "⚠️ No tests found for $$package"; \
		fi; \
	done
	@echo "✅ Testing complete!"

# Clean up build artifacts
clean:
	@for package in $(PACKAGES); do \
		echo "🧹 Cleaning $$package..."; \
		cd $$package && poetry cache clear --all pypi && rm -rf dist build && cd ..; \
	done
	@echo "✅ Cleanup complete!"

# Run all steps in order
setup: install develop build test
