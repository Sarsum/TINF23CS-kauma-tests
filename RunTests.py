import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Helper script to run the tests of the testing repository")
    parser.add_argument("kauma", help="Path to the kauma executable")
    parser.add_argument("--ignore-test-failures", action='store_true', help="Does not exit with an error when tests fail")
    parser.add_argument("-f", "--filter", action="append", dest="filters",
                        help="Optional substring filter for test names. Can be used multiple times. "
                             "Only tests whose relative path contains any given filter will be run.")
    args = parser.parse_args()

    print(args.kauma)

    base_dir = Path(__file__).resolve().parent
    work_dir = Path(os.getcwd())
    tests_dir = base_dir / "tests"
    testresults = {}
    failed_test = False

    # Keep track whether any test matched the filters (used for warning after for loop)
    any_matched = False

    for file_path in tests_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(tests_dir).__str__()

            # If filters provided, only run files whose relative path contains at least one filter substring
            if args.filters:
                matched = any(filt in relative_path for filt in args.filters)
                if not matched:
                    print(f"Skipping {relative_path} (does not match filters: {args.filters})")
                    continue
                any_matched = True

            testresults[relative_path] = {"successful": [], "failed": [], "missing": []}
            with open(file_path, 'r') as file:
                testdata = json.load(file)
            start = datetime.datetime.now()
            proc = subprocess.Popen([work_dir / args.kauma, file_path],stdout=subprocess.PIPE)
            output = proc.stdout.read()
            end = datetime.datetime.now()
            for line in output.decode(encoding="UTF-8").split("\n"):
                if not line:
                    continue
                result = json.loads(line)
                if result['reply'] == testdata['expectedResults'][result['id']]:
                    testresults[relative_path]['successful'] += [result['id']]
                else:
                    testresults[relative_path]['failed'] += [result['id']]
                    failed_test = True
                testdata['expectedResults'].pop(result['id'])
            testresults[relative_path]['timeSeconds'] = f"{(end - start).total_seconds():.3f}"
            for k in testdata['expectedResults']:
                if testdata['expectedResults'][k] is None:
                    testresults[relative_path]['successful'] += [k]
                else:
                    testresults[relative_path]['missing'] += [k]

    if args.filters and not any_matched:
        print(f"Warning: no tests matched the filters {args.filters}")
    else:
        rows = []
        for k in testresults:
            rows += [[k, len(testresults[k]["successful"]), len(testresults[k]["failed"]),
                        len(testresults[k]["missing"]), testresults[k]["timeSeconds"], testresults[k]["failed"][:4] 
                        if len(testresults[k]["failed"]) != 0 else None, testresults[k]["missing"][:4] if 
                        len(testresults[k]["missing"]) != 0 else None ]]
            
        header = ["Testfile", "Successful", "Failed (C)", "Missing (C)",
                        "Time Seconds", "Failed (T)", "Missing (T)"]
        widths = [max(len(str(row[i])) for row in [header] + rows) for i in range(len(header))]

        # Print header
        print(" | ".join(str(header[i]).ljust(widths[i]) for i in range(len(header))))
        print("-+-".join("-" * widths[i] for i in range(len(header))))

        # Print rows
        for row in rows:
            print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(row))))

        print("\nC: Count\nT: Task")

        if not args.ignore_test_failures:
            sys.exit(failed_test)


main()