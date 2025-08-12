# 🧪 Marketing Chat Agent - Test Suite

Comprehensive testing framework for development and QA workflows.

## 📁 Test Structure

```
tests/
├── unit/                          # 🔬 Micro-level component tests
│   ├── test_text_only_agent.py    # Text generation tests
│   ├── test_image_only_agent.py   # Image generation tests
│   └── test_hashtag_only_agent.py # Hashtag/CTA generation tests
├── integration/                   # 🔗 Full workflow tests
│   ├── test_full_marketing_flow.py      # Complete campaigns
│   └── test_multichannel_delivery.py    # Multi-platform delivery
├── utils/                         # 🛠️ Shared test utilities
│   └── test_helpers.py           # Common functions & validators
├── dev_test_runner.py            # 🚀 Fast development tests
├── qa_test_runner.py             # 🔍 Comprehensive QA tests
├── run_tests.py                  # 🎮 Main test controller
└── reports/                      # 📊 Test execution reports
```

## 🎯 Quick Start

### Development Workflow
```bash
# Quick validation before commit
make test-dev

# Basic system check
make test-smoke

# Clean up test files
make clean
```

### QA Workflow
```bash
# Comprehensive testing
make test-qa

# Full test suite
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration
```

## 🧪 Test Types

### 🔬 Unit Tests
**Purpose**: Test individual micro agents in isolation

**Coverage**:
- `TextOnlyAgent`: Text generation functionality
- `ImageOnlyAgent`: Image generation functionality  
- `HashtagOnlyAgent`: Hashtag and CTA generation

**Test Cases per Agent**:
- Basic functionality
- Seasonal context preservation
- Detailed campaign parameters
- B2B scenarios
- Cultural context handling
- Error handling
- Metadata tracking

### 🔗 Integration Tests
**Purpose**: Test complete marketing workflows

**Coverage**:
- End-to-end campaign generation
- Multi-channel delivery
- AI review and approval process
- File organization and structure
- Performance validation

### 🚀 Development Tests
**Purpose**: Fast feedback for developers

**Features**:
- Quick agent validation (< 30s)
- Performance timing
- Error detection
- Pre-commit verification

### 🔍 QA Tests
**Purpose**: Production readiness validation

**Features**:
- Comprehensive test coverage
- Detailed reporting (JSON format)
- Performance analysis
- Quality gates validation

## 📊 Test Results

### Development Test Output
```
🧪 DEVELOPMENT TEST SUITE - QUICK VALIDATION
============================================================

🔬 MICRO AGENT TESTS
✅ PASS TextOnlyAgent (10.99s) - Generated 373 chars
✅ PASS ImageOnlyAgent (50.58s) - Image: generated_xxx.png
✅ PASS HashtagOnlyAgent (17.85s) - 10 hashtags, 3 CTAs

🔗 INTEGRATION TEST
✅ PASS Full Marketing Flow (45.23s) - Delivered to 3 channels

🎉 ALL DEV TESTS PASSED! Ready to commit! ✅
```

### QA Test Output
```
🔍 QA TEST SUITE - COMPREHENSIVE VALIDATION
====================================
📊 COMPONENT BREAKDOWN
  ✅ TextOnlyAgent: 5/5 tests passed
  ✅ ImageOnlyAgent: 5/5 tests passed  
  ✅ HashtagOnlyAgent: 5/5 tests passed
  ✅ Integration: 5/5 tests passed

✅ Tests Passed: 20/20
📈 Success Rate: 100.0%
📄 QA Report saved: tests/reports/qa_report_20241211_143022.json
```

## 🔧 Test Configuration

### Environment Variables
```bash
# Required for testing
export DRY_RUN=true
export ENABLE_EMAIL=true
export ENABLE_INSTAGRAM=true
export ENABLE_FACEBOOK=true
export OPENAI_API_KEY=your_key_here
```

### Test Data
The test suite uses predefined sample inputs:
- Simple campaigns
- Seasonal promotions (New Year, Diwali, Christmas)
- Multi-channel campaigns
- B2B scenarios
- Cultural context campaigns

## 🎮 Available Commands

| Command | Purpose | Speed | Coverage |
|---------|---------|-------|----------|
| `make test-dev` | Development | ⚡ Fast | Core functionality |
| `make test-smoke` | Sanity check | ⚡ Fastest | Basic imports |
| `make test-unit` | Unit testing | 🔄 Medium | Individual components |
| `make test-integration` | Integration | 🔄 Medium | Full workflows |
| `make test-qa` | QA validation | 🐌 Comprehensive | Production ready |
| `make test` | Everything | 🐌 Comprehensive | Complete coverage |

## 📈 Performance Benchmarks

**Target Performance**:
- Unit tests: < 30s per agent
- Integration tests: < 60s per workflow
- Development suite: < 2 minutes total
- QA suite: < 10 minutes total

**Current Results**:
- ✅ TextOnlyAgent: ~11s
- ✅ ImageOnlyAgent: ~51s (includes API calls)
- ✅ HashtagOnlyAgent: ~18s
- ⚠️ Integration: Variable (depends on AI review)

## 🔍 Quality Gates

### Development Gates
- All micro agents pass basic functionality
- No import errors
- Performance within reasonable bounds

### QA Gates
- 100% test pass rate
- All components validated
- Performance benchmarks met
- Comprehensive test coverage
- Detailed reporting generated

## 🛠️ Test Utilities

### TestResultValidator
Validates agent outputs:
```python
validator = TestResultValidator(result)
validator.validate_text_generation()    # ✅ Text content validation
validator.validate_image_generation()   # ✅ Image URL validation  
validator.validate_hashtag_generation() # ✅ Hashtag format validation
validator.validate_full_campaign()      # ✅ Complete workflow validation
```

### Sample Test Data
```python
SAMPLE_INPUTS = {
    "simple": "promote smartphones",
    "seasonal": "promote fitness app on new year", 
    "multichannel": "sell smart watches on instagram facebook email",
    "detailed": "promote organic skincare to young women on instagram with engaging tone $500 budget"
}
```

## 🔄 CI/CD Integration

```bash
# Pipeline example
make clean          # Clean environment
make setup          # Prepare test environment  
make test-smoke     # Quick sanity check
make test-unit      # Validate components
make test-integration # Validate workflows
make test-qa        # Full QA validation
```

## 📊 Reporting

### JSON Reports
QA tests generate detailed JSON reports in `tests/reports/`:
```json
{
  "timestamp": "2024-12-11 14:30:22",
  "summary": {
    "total_tests": 20,
    "passed_tests": 20,
    "success_rate": 100.0,
    "total_time": 234.56
  },
  "components": {
    "TextOnlyAgent": { ... },
    "ImageOnlyAgent": { ... },
    "Integration": { ... }
  }
}
```

## 🎯 Next Steps

1. **Expand Test Coverage**: Add more edge cases
2. **Performance Optimization**: Improve test execution speed
3. **Mock Integration**: Add mocks for faster unit tests
4. **CI/CD Integration**: Integrate with build pipelines
5. **Visual Reports**: Generate HTML test reports

---

**🎉 Happy Testing! The test suite ensures reliable, high-quality marketing agent functionality.** 🚀
