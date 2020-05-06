
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

def get_config_element_from_line(line, line_nr):
    line = line.strip()
    config_ele = line[line.find("config.get") + len("config.get"):]
    ele_type = config_ele[1:config_ele.find("(")]
    if not ele_type:
        return None
    between_parenthesis = config_ele[config_ele.find("(")+1: config_ele.find(")")]
    default_val = None
    if "," in between_parenthesis:
        # has a default value
        split_pos = between_parenthesis.find(",")
        key_word, default_val = between_parenthesis[:split_pos], between_parenthesis[split_pos+1:]
        default_val = default_val.strip()
    else:
        key_word = between_parenthesis
    key_word = key_word.strip()
    if "\"" in key_word:
        sep = "\""
    else:
        sep = "'"
    key_word = key_word.replace(sep, "")
    if key_word:
        return ConfigElement(key_word, ele_type, line, line_nr, default_val)
    else:
        return None

def get_config_value_from_csv_line(line, line_nr):
    line = line.strip()
    key_word = line[line.find("\"") + 1:]
    key_word = key_word[:key_word.find("\"")].strip()
    if key_word:
        return ConfigElement(key_word, None, line, line_nr, None)
    else:
        return None

class ConfigElement(object):

    def __init__(self, key_word, ele_type, line, line_nr, default_val):
        self.key_word = key_word.strip()
        self.ele_type = ele_type
        self.default_value = default_val
        self.line = line
        self.line_nr = line_nr
        self.found_usage = None

    def __repr__(self):
        if self.default_value:
            return str("{}({}): {}".format(self.key_word, self.ele_type, self.default_value))
        else:
            return str("{}({})".format(self.key_word, self.ele_type))

    def set_type(self, line):
        if "Type:" in line:
            ele_type = line[line.find("Type:") + len("Type:"):]
            ele_type = ele_type.strip()
            if "Default" in ele_type:
                poses = [ele_type.find("Default"), ele_type.find(".Default"), ele_type.find(". Default"),
                         ele_type.find(",Default"), ele_type.find(", Default")]
            else:
                poses = [ele_type.find("."), ele_type.find(" "), ele_type.find(", ")]
            poses = [ele for ele in poses if ele > 0]
            if poses:
                end_pos = min(poses)
                ele_type = ele_type[:end_pos]
            if ele_type:
                self.ele_type = ele_type

    def set_default(self, line):
        if "Default:" in line:
            default_val = line[line.find("Default:") + len("Default:"):]
            default_val = default_val.strip()
            poses = [default_val.find("."), default_val.find(" "), default_val.find(", ")]
            if poses:
                end_pos = min(poses)
                default_val = default_val[:end_pos]
            if default_val:
                self.default_value = default_val



if __name__ == "__main__":

    all_py_files = find_all_py_files(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))
    for py_file in all_py_files:
        if "scripts" not in os.path.abspath(py_file):
            with open(py_file, "r") as file:
                errors = []
                base_name = os.path.basename(py_file)
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
                list_of_used_config_get = []
                if found_config_values:
                    # checks if there are config values not defined at the top
                    for line_nr, line in enumerate(lines):
                        org_line = line
                        if "config.get" in line:
                            org_line = org_line[org_line.find("config.get"):]
                            org_line = org_line[:org_line.find(")")+1]
                            config_element = get_config_element_from_line(line, line_nr)
                            if config_element:
                                key_word = config_element.key_word
                                if " " not in key_word and key_word != "key":
                                    list_of_used_config_get.append(config_element)
                                    if key_word not in found_config_values:
                                        errors.append("Not found at the top: '{}' " \
                                                      "in L:{} '{}'".format(config_element.key_word,
                                                                        line_nr, org_line.strip()))
                start_csv_table = False
                start_new_config_value = False
                current_element = None
                # check if each key_word has a Type:
                for line_nr, line in enumerate(lines):
                    if ":header:" in line:
                        continue
                    if "csv-table" in line:
                        start_csv_table = True
                    elif start_csv_table and ("__init__" in line or line.strip() == '"""'):
                        if current_element and current_element.ele_type is None:
                            errors.append("This key '{}' does not have a Type".format(
                                current_element.key_word))
                        break
                    if start_csv_table:
                        config_element = get_config_value_from_csv_line(line, line_nr)
                        if config_element and " " not in config_element.key_word and config_element.key_word != "key":
                            found_values = [ele for ele in list_of_used_config_get if
                                            ele.key_word == config_element.key_word]
                            if found_values:
                                config_element.found_usage = found_values
                            if current_element:
                                # found a new key_word, check the last one
                                if current_element.ele_type is None:
                                    if current_element.found_usage:
                                        errors.append(
                                            "This key '{}' does not have a Type, used type in code: {}".format(current_element.key_word, [ele.ele_type for ele in current_element.found_usage]))
                                    else:
                                        errors.append("This key '{}' does not have a Type".format(current_element.key_word))
                                if current_element.default_value:
                                    if current_element.found_usage:
                                        for found_value in current_element.found_usage:
                                            f_default_v = found_value.default_value
                                            if f_default_v != current_element.default_value:
                                                ele_type = current_element.ele_type.lower()
                                                if ele_type == "int" or ele_type == "float":
                                                    if f_default_v.isnumeric() and current_element.default_value.isnumeric():
                                                        errors.append("The default value does not match the value in the " \
                                                                      "docu for key: {} ({}!={})".format(
                                                                                                 current_element.key_word,
                                                                                                 current_element.default_value,
                                                                                             f_default_v))
                            current_element = config_element
                        if current_element:
                            # there is no new key found, and there was an old key there
                            if "Type:" in line:
                                current_element.set_type(line)
                            if "Default:" in line:
                                current_element.set_default(line)
                if errors:
                    print("In {}: \n{}".format(base_name, "\n".join(["   "+ele for ele in errors])))













