# KAUMA course test repository
This repository contains **testcases** for the `kauma` tool developed in the KAuMA course of 2025.
It serves as a central repository to share testcases across both courses.

## Structure
```
├── schema.json         # JSON schema defining the structure of all test files
└── tests/              # Directory containing all exercise test files (currently empty)
```
* `schema.json` – Specifies the required structure, data types, and constraints for each test file.
All test definitions must conform to this schema.
* `tests/` – Contains JSON files with test data for individual exercises, typically named after their purpose.

## Test File Format
Each test file must validate against the schema defined in `schema.json`.
This ensures consistency and compatibility across all users of this repository.

### Example (simplified)
```json
{
    "title": "Some title",
    "description": "Description of the tests",
    "authors": ["optionally", "authors"],
    "testcases": {
        "test1": {
            "action": "action1",
            "arguments": {
                "someString": "example",
                "someObject": {
                    
                }
            }
        },
        "test2": {
            "action": "action1",
            "arguments": {
                "otherString": "example"
            }
        }
    },
    "expectedResult": {
        "responses": {
            "test1": {...response object as expected for the action...},
            "test2": null
        }
    }
}
```
> For the full specification, see `schema.json`

## Validation
Before submitting or committing new test files, ensure they pass validation against the schema.

Using Python (`jsonschema`):
```
pip install jsonschema
python -m jsonschema -i tests/exercise1.json schema.json
```

All test files must be valid before merging into the repository.

## Contribution Guidelines

1. Fork this repository.
2. Add your test file(s) under `tests/`, following the schema format.
3. Validate your test file locally using one of the methods above.
4. Open a Pull Request including:
    * A brief description of the exercise.
    * Any relevant notes or special cases.