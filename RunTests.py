import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Helper script to run the tests of the testing repository")
    parser.add_argument("kauma", help="Path to the kauma executable")
    args = parser.parse_args()

    print(args.kauma)

    base_dir = Path(__file__).resolve().parent
    work_dir = Path(os.getcwd())
    tests_dir = base_dir / "tests"
    testresults = {}
    for file_path in tests_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(tests_dir).__str__()
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
                testdata['expectedResults'].pop(result['id'])
            testresults[relative_path]['timeMillis'] = (end - start).microseconds / 1000
            for k in testdata['expectedResults']:
                if testdata['expectedResults'][k] == None:
                    testresults[relative_path]['successful'] += [k]
                else:
                    testresults[relative_path]['missing'] += [k]
    result_table = [["Testfile", "Successfull (Count)", "Failed (Count)", "Missing (Count)",
                     "Time Millis", "Failed (Tasks)", "Missing (Tasks)"]]
    for k in testresults:
        result_table += [[k, len(testresults[k]["successful"]), len(testresults[k]["failed"]),
                       len(testresults[k]["missing"]), testresults[k]["timeMillis"], testresults[k]["failed"],
                       testresults[k]["missing"]]]
    for row in result_table:
        print(",".join(str(x) for x in row))

main()