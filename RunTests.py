import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile # Added for temporary file creation

def main():
    parser = argparse.ArgumentParser(description="Helper script to run the tests of the testing repository")
    parser.add_argument("kauma", help="Path to the kauma executable")
    parser.add_argument("--ignore-test-failures", action='store_true', help="Does not exit with an error when tests fail")
    parser.add_argument("-f", "--filter", action="append", dest="filters",
                        help="Optional substring filter for test names. Can be used multiple times. "
                             "Only tests whose relative path contains any given filter will be run.")
    parser.add_argument("-s", "--sidecar", action="append", dest="sidecars",
                        help="Specify available sidecars. Tests requiring others will be skipped. "
                             "Can be used multiple times, e.g. -s crypto -s network")
    parser.add_argument("--python", dest="python_blacklist",
                        help="Path to a text file blacklist. Tests with relative paths "
                             "matching any line in this file will be skipped. "
                             "Paths should use forward slashes (/) as separators.")
    parser.add_argument("--delimiter", dest="testcase_limit", type=int,
                        help="Limit the number of test cases to run from each file. "
                             "Runs only the first N test cases found in the file.")
    args = parser.parse_args()

    # --- Loading Screen (prints to stderr) ---
    print("--- Kauma Test Runner Initializing ---", file=sys.stderr)
    print(f"Kauma executable: {args.kauma}", file=sys.stderr)
    if args.filters:
        print(f"Applying filters: {args.filters}", file=sys.stderr)
    if args.sidecars:
        print(f"Available sidecars: {args.sidecars}", file=sys.stderr)
    
    python_blacklist_set = set()
    if args.python_blacklist:
        print(f"Loading Python blacklist from: {args.python_blacklist}", file=sys.stderr)
        try:
            blacklist_path = Path(args.python_blacklist).resolve()
            with open(blacklist_path, 'r') as f:
                python_blacklist_set = {
                    Path(line.strip()).as_posix() 
                    for line in f if line.strip()
                }
            print(f"Loaded {len(python_blacklist_set)} files to blacklist.", file=sys.stderr)
        except FileNotFoundError:
            print(f"Error: Blacklist file not found: {blacklist_path}", file=sys.stderr)
            sys.exit(1)

    if args.testcase_limit:
        print(f"Applying test case limit (delimiter): {args.testcase_limit}", file=sys.stderr)

    print("--------------------------------------", file=sys.stderr)

    base_dir = Path(__file__).resolve().parent
    work_dir = Path(os.getcwd())
    tests_dir = base_dir / "tests"
    testresults = {}
    failed_test = False

    any_matched = False
    available_sidecars = args.sidecars or []

    print(f"Scanning for tests in {tests_dir}...", file=sys.stderr)

    for file_path in tests_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(tests_dir).as_posix()

            if relative_path in python_blacklist_set:
                print(f"Skipping {relative_path} (in python blacklist)", file=sys.stderr)
                continue

            if args.filters:
                matched = any(filt in relative_path for filt in args.filters)
                if not matched:
                    print(f"Skipping {relative_path} (does not match filters: {args.filters})", file=sys.stderr)
                    continue
                any_matched = True

            with open(file_path, 'r') as file:
                try:
                    testdata = json.load(file)
                except json.JSONDecodeError as e:
                    print(f"Skipping {relative_path} (Invalid JSON: {e})", file=sys.stderr)
                    continue

            required_sidecars = testdata.get("requiredSidecars", [])
            if required_sidecars:
                missing = [s for s in required_sidecars if s not in available_sidecars]
                if missing:
                    print(f"Skipping {relative_path} (missing required sidecars: {missing})", file=sys.stderr)
                    continue
            
            # --- NEW: Delimiter/Limit Logic ---
            file_path_to_run = file_path # Default to original file
            tmp_file_to_delete = None

            # Check if the limit is set and if this file has more test cases than the limit
            if args.testcase_limit and len(testdata.get("testcases", {})) > args.testcase_limit:
                print(f"Limiting {relative_path} to first {args.testcase_limit} test cases.", file=sys.stderr)
                
                # Get the first N testcase IDs (relies on Python 3.7+ dict insertion order)
                testcase_ids_to_keep = list(testdata["testcases"].keys())[:args.testcase_limit]
                
                # Filter both testcases and expectedResults in the loaded 'testdata' variable
                testdata["testcases"] = {
                    k: testdata["testcases"][k] for k in testcase_ids_to_keep
                }
                
                original_expected = testdata.get("expectedResults", {})
                testdata["expectedResults"] = {
                    k: original_expected.get(k) 
                    for k in testcase_ids_to_keep # Only keep expected results for the test cases we are running
                }
                
                # Create a temporary file to pass to kauma
                try:
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json", encoding='utf-8') as tmp_f:
                        json.dump(testdata, tmp_f)
                        file_path_to_run = Path(tmp_f.name) # Use Path object for Popen
                        tmp_file_to_delete = file_path_to_run
                except Exception as e:
                    print(f"*** Error creating temp file for {relative_path}: {e} ***", file=sys.stderr)
                    continue # Skip this test file

            # --- End of New Logic ---

            testresults[relative_path] = {"successful": [], "failed": [], "missing": []}

            print(f"Running test: {relative_path}...", file=sys.stderr)
            
            start = datetime.datetime.now()
            # Use file_path_to_run (which is either the original or the temp file)
            proc = subprocess.Popen([work_dir / args.kauma, file_path_to_run], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, stderr_output = proc.communicate()
            end = datetime.datetime.now()

            # --- NEW: Cleanup for temp file ---
            if tmp_file_to_delete:
                try:
                    tmp_file_to_delete.unlink() # Delete the temp file
                except OSError as e:
                    print(f"*** Warning: could not delete temp file {tmp_file_to_delete}: {e} ***", file=sys.stderr)
            # --- End Cleanup ---

            if stderr_output:
                print(f"*** Error from kauma ({relative_path}): {stderr_output.decode(encoding='UTF-8').strip()} ***", file=sys.stderr)

            # The rest of this logic now correctly uses the modified 'testdata' (if it was truncated)
            for line in output.decode(encoding="UTF-8").split("\n"):
                if not line:
                    continue
                try:
                    result = json.loads(line)
                except json.JSONDecodeError:
                    print(f"*** Failed to decode JSON output from kauma: {line} ***", file=sys.stderr)
                    failed_test = True
                    continue

                if 'id' not in result or 'reply' not in result:
                    print(f"*** Invalid result format from kauma: {line} ***", file=sys.stderr)
                    failed_test = True
                    continue

                # Check against the (potentially truncated) expectedResults
                if result['id'] not in testdata.get('expectedResults', {}):
                    print(f"*** Received unexpected result ID from kauma: {result['id']} ***", file=sys.stderr)
                    failed_test = True
                    continue

                if result['reply'] == testdata['expectedResults'][result['id']]:
                    testresults[relative_path]['successful'] += [result['id']]
                else:
                    testresults[relative_path]['failed'] += [result['id']]
                    failed_test = True
                testdata['expectedResults'].pop(result['id']) # Pop from the (potentially truncated) dict

            testresults[relative_path]['timeSeconds'] = f"{(end - start).total_seconds():.3f}"
            # This loop correctly iterates over the remaining items in the (potentially truncated) dict
            for k in testdata.get('expectedResults', {}):
                if testdata['expectedResults'][k] is None:
                    testresults[relative_path]['successful'] += [k]
                else:
                    testresults[relative_path]['missing'] += [k]

    print("--- Test run complete. Generating summary... ---", file=sys.stderr)

    if args.filters and not any_matched:
        print(f"Warning: no tests matched the filters {args.filters}", file=sys.stderr)
    elif not testresults:
        if not (args.filters and not any_matched):
            print("No test files were found or matched the given filters.", file=sys.stderr)
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

        print("\n" + " | ".join(str(header[i]).ljust(widths[i]) for i in range(len(header))))
        print("-+-".join("-" * widths[i] for i in range(len(header))))

        for row in rows:
            print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(row))))

        print("\nC: Count\nT: Task")

        if failed_test:
            print("\n--- SOME TESTS FAILED ---", file=sys.stderr)
        else:
            print("\n--- ALL TESTS PASSED ---", file=sys.stderr)

        if not args.ignore_test_failures:
            sys.exit(1 if failed_test else 0)


if __name__ == "__main__":
    main()
