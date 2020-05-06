

import glob
import os

def find_all_py_files(folder_path):
    res = []
    for file_path in os.listdir(folder_path):
        current_file = os.path.join(folder_path, file_path)
        if os.path.isfile(current_file) and current_file.endswith(".py"):
            res.append(current_file)
        elif os.path.isdir(current_file):
            res.extend(find_all_py_files(current_file))
    return res

def get_config_value_from_config_line(line):
    line = line.strip()
    if "\"" in line:
        sep = "\""
    else:
        sep = "'"
    line = line[line.find("config.get") + len("config.get"):]
    line = line[line.find(sep) + 1:]
    line = line[:line.find(sep)].strip()

    return line

def get_config_value_from_csv_line(line):
    line = line.strip()
    line = line[line.find("\"") + 1:]
    line = line[:line.find("\"")].strip()
    return line


if __name__ == "__main__":

    all_py_files = find_all_py_files(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))
    for py_file in all_py_files:
        if "scripts" not in os.path.abspath(py_file):
            with open(py_file, "r") as file:
                lines = file.read().split("\n")
                found_config_values = []
                start_csv_table = False
                for line in lines:
                    if "csv-table" in line:
                        start_csv_table = True
                    elif start_csv_table and "__init__" in line:
                        break
                    if start_csv_table:
                        line = line.strip()
                        if line and "\", \"" in line and not ":header:" in line:
                            line = line[line.find("\"") + 1:]
                            line = line[:line.find("\"")].strip()
                            if line:
                                found_config_values.append(line)

                if found_config_values:
                    # checks if there are config values not defined at the top
                    for line_nr, line in enumerate(lines):
                        org_line = line
                        if "config.get" in line:
                            org_line = org_line[org_line.find("config.get"):]
                            org_line = org_line[:org_line.find(")")+1]
                            line = get_config_value_from_config_line(line)
                            if " " not in line and line != "key":
                                if line not in found_config_values:
                                    print("In {}: Not found at the top: {} in L:{} '{}'".format(os.path.basename(py_file), line, line_nr, org_line.strip()))
                start_csv_table = False
                start_new_config_value = False
                current_keyword = None
                for line in lines:
                    if ":header:" in line:
                        continue
                    if "csv-table" in line:
                        start_csv_table = True
                    elif start_csv_table and "__init__" in line:
                        if current_keyword:
                            print("In {}: This key {} does not have a Type".format(
                                os.path.basename(py_file), current_keyword))
                        break
                    if start_csv_table:
                        keyword = get_config_value_from_csv_line(line)
                        if keyword and " " not in keyword and keyword != "key":
                            # found a new keyword
                            if current_keyword:
                                print("In {}: This key {} does not have a Type".format(os.path.basename(py_file), current_keyword))
                                current_keyword = None
                            if "Type" not in line:
                                current_keyword = keyword
                        elif current_keyword:
                            # there is no new key found, and there was an old key found
                            if "Type" in line:
                                # check if the old key is ended here
                                current_keyword = None
                                continue













