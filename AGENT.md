Project Agent Configuration
Purpose
This agent operates at the root level of the project with strict file creation restrictions. The agent can only create its own test scripts, temporary files, and documentation within the tmp/agent/ directory, which is located in the tmp/ directory at the project root. The tmp/ directory is the sole location for all scratch and test-related file creation.
File Creation Restrictions
Allowed Directory

ONLY: tmp/agent/ - Agent's isolated workspace, located within tmp/ in the project root
The tmp/ directory in the project root is the only place where the agent can create files, specifically within its tmp/agent/ sandbox

Prohibited Locations

❌ Root directory - No files created directly in project root
❌ Source directories - No modifications to existing code structure
❌ packages/ - Managed by separate Poetry Packages Agent
❌ scripts/ - No test scripts or other files to be created here
❌ Any other project directories - Strictly forbidden

Permitted Operations in tmp/agent/
Test Scripts

Create test scripts to validate project functionality
Generate temporary test data files
Build proof-of-concept scripts for experimentation
Create validation scripts for project components

Documentation and Reports

Generate run summaries and execution reports
Create analysis documents of project state
Build temporary documentation for testing purposes
Generate logs and diagnostic files

Temporary Files

Cache files for agent operations
Intermediate processing files
Backup copies of generated content
Temporary configuration files for testing

Directory Structure
project-root/
├── tmp/                       # Located in project root, contains agent's workspace
│   └── agent/                 # Agent's exclusive workspace
│       ├── tests/            # Test scripts
│       ├── docs/             # Generated documentation
│       ├── reports/          # Run summaries and analysis
│       ├── cache/            # Temporary cache files
│       └── scratch/          # Experimental/scratch files
├── packages/                  # Managed by Poetry Packages Agent
├── scripts/                  # READ-ONLY, no test scripts here
├── [other project files]     # READ-ONLY for this agent
└── AGENT.md                  # This configuration file

Agent Behavior Rules
File Creation Protocol

Always check: Is the target path within tmp/agent/ in the project root's tmp/ directory?
If YES: Proceed with file creation
If NO: Abort operation and explain restriction

Read Operations

Agent can READ any file in the project for analysis
Agent can inspect project structure and dependencies
Agent can analyze existing code and configurations

Write Operations

Agent can WRITE only within tmp/agent/ directory, located in tmp/ at the project root
Agent must create tmp/ and tmp/agent/ if they don't exist
Agent can organize files within subdirectories of tmp/agent/

Typical Use Cases
Testing and Validation
project-root/tmp/agent/tests/
├── validate_packages.py       # Test all Poetry packages
├── dependency_check.py        # Verify dependencies
├── build_test.py             # Test package builds
└── integration_test.py       # Full project integration test

Documentation Generation
project-root/tmp/agent/docs/
├── project_summary.md         # Project overview
├── package_inventory.md       # List of all packages
├── dependency_map.md          # Dependency relationships
└── health_report.md          # Project health status

Run Reports
project-root/tmp/agent/reports/
├── 2025-08-07_analysis.md     # Daily project analysis
├── package_validation_log.txt # Validation results
├── error_summary.json        # Collected errors
└── recommendations.md         # Improvement suggestions

Safety Measures
Pre-Creation Checks
Before creating any file, the agent must:

Verify the target path starts with tmp/agent/ within the project root's tmp/ directory
Create the tmp/ and tmp/agent/ directory structure if it doesn't exist
Ensure no conflicts with existing project structure

Error Handling

If agent attempts to create files outside tmp/agent/: STOP and explain
If tmp/ or tmp/agent/ cannot be created: Report error and abort
If file conflicts occur within tmp/agent/: Overwrite or rename safely

Cleanup Guidelines

Agent should organize files logically within tmp/agent/
Use timestamps in filenames to avoid conflicts
Clean up old files periodically if requested

Integration with Other Agents
Poetry Packages Agent

This root agent can READ from packages/ for analysis
This root agent can generate reports about Poetry packages in tmp/agent/
Poetry Packages Agent handles all modifications to packages/

Coordination Protocol

Root agent provides analysis and testing
Specialized agents (like Poetry Packages Agent) handle specific directories
All agents respect each other's boundaries

Violation Protocol
If Agent Attempts Prohibited Actions

Immediate Stop: Halt the file creation operation
Clear Explanation: Explain why the action is prohibited
Alternative Suggestion: Propose creating the file in tmp/agent/ within the project root's tmp/ directory
Seek Confirmation: Ask user if the alternative is acceptable

Example Response to Violation Attempt
⚠️ RESTRICTION VIOLATION DETECTED

Attempted action: Create "requirements.txt" in project root or "test_script.py" in scripts/
Status: BLOCKED

Reason: This agent can only create files in tmp/agent/ directory within the project root's tmp/ directory. The scripts/ directory is reserved for other purposes.

Alternative: I can create tmp/agent/tests/test_script.py or tmp/agent/analysis/requirements_analysis.txt 
to document the requirements or test scripts I would have generated.

Proceed with alternative? [Y/N]

File Naming Conventions
Timestamps

Use ISO format: YYYY-MM-DD_filename.ext
For multiple runs per day: YYYY-MM-DD_HHMMSS_filename.ext

Categories

Tests: test_*.py or validate_*.py
Reports: *_report.md or *_summary.md
Docs: *_doc.md or *_guide.md
Scratch: scratch_*.py or temp_*.txt

Success Metrics

Zero files created outside tmp/agent/ directory in the project root's tmp/ directory
Organized file structure within allowed directory
Clear, useful test scripts and documentation
No interference with existing project structure
Helpful analysis and reporting capabilities
