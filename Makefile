# Makefile for Marketing Chat Agent Development & QA

.PHONY: help test test-unit test-integration test-dev test-qa test-smoke clean setup

# Default target
help:
	@echo "🧪 Marketing Chat Agent - Test Commands"
	@echo "======================================"
	@echo ""
	@echo "🔧 Development Commands:"
	@echo "  make test-dev     - Quick development tests (fast feedback)"
	@echo "  make test-smoke   - Basic smoke tests (sanity check)"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  make test         - Run all tests (unit + integration)"
	@echo "  make test-unit    - Run unit tests only (micro agents)"
	@echo "  make test-integration - Run integration tests only (full flows)"
	@echo ""
	@echo "🔍 QA Commands:"
	@echo "  make test-qa      - Comprehensive QA tests (production ready)"
	@echo ""
	@echo "🧹 Utility Commands:"
	@echo "  make clean        - Clean up test files and outputs"
	@echo "  make setup        - Set up test environment"

# Development workflow - fast tests for developers
test-dev:
	@echo "🚀 Running Development Tests..."
	python tests/dev_test_runner.py

# Basic smoke test - verify system is working
test-smoke:
	@echo "💨 Running Smoke Tests..."
	python tests/run_tests.py --mode smoke

# Run all tests
test:
	@echo "🧪 Running All Tests..."
	python tests/run_tests.py --mode all --cleanup

# Unit tests only
test-unit:
	@echo "🔬 Running Unit Tests..."
	python tests/run_tests.py --mode unit --cleanup

# Integration tests only  
test-integration:
	@echo "🔗 Running Integration Tests..."
	python tests/run_tests.py --mode integration --cleanup

# Comprehensive QA tests
test-qa:
	@echo "🔍 Running QA Tests..."
	python tests/qa_test_runner.py

# Clean up test artifacts
clean:
	@echo "🧹 Cleaning up test files..."
	rm -rf data/outbox/*
	rm -rf static/images/*.png
	rm -rf tests/reports/*
	rm -rf tests/__pycache__
	rm -rf tests/*/__pycache__
	rm -rf tests/*/*/__pycache__

# Set up test environment
setup:
	@echo "⚙️ Setting up test environment..."
	mkdir -p data/outbox
	mkdir -p static/images
	mkdir -p tests/reports
	@echo "✅ Test environment ready"

# Quick agent tests
test-agents:
	@echo "🤖 Testing Individual Agents..."
	@echo "📝 Text Agent:"
	python -c "from tests.dev_test_runner import quick_agent_test; from src.agents.micro.text_only_agent import TextOnlyAgent; print('✅' if quick_agent_test(TextOnlyAgent, 'TextOnlyAgent', 'test product')['success'] else '❌')"
	@echo "🖼️ Image Agent:"
	python -c "from tests.dev_test_runner import quick_agent_test; from src.agents.micro.image_only_agent import ImageOnlyAgent; print('✅' if quick_agent_test(ImageOnlyAgent, 'ImageOnlyAgent', 'test product')['success'] else '❌')"
	@echo "🏷️ Hashtag Agent:"
	python -c "from tests.dev_test_runner import quick_agent_test; from src.agents.micro.hashtag_only_agent import HashtagOnlyAgent; print('✅' if quick_agent_test(HashtagOnlyAgent, 'HashtagOnlyAgent', 'test product')['success'] else '❌')"

# CI/CD pipeline test
test-ci:
	@echo "🔄 Running CI/CD Pipeline Tests..."
	make clean
	make setup
	make test-smoke
	make test-unit
	make test-integration
	@echo "🎉 CI/CD Tests Complete!"

# Performance test
test-perf:
	@echo "⚡ Running Performance Tests..."
	time make test-dev
	@echo "📊 Performance test complete"
