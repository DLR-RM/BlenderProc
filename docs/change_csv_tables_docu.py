
import os
import argparse

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
    if "own_config" in line:
        return None
    config_ele = line[line.find("config.get") + len("config.get"):]
    ele_type = config_ele[1:config_ele.find("(")]
    if not ele_type:
        return None
    if config_ele.count("(") == 1:
        between_parenthesis = config_ele[config_ele.find("(")+1: config_ele.find(")")]
    else:
        between_parenthesis = config_ele[config_ele.find("(")+1:]
        if ")" in between_parenthesis:
            next_closing_pos, next_opening_pos = 0, 0
            for _ in range(config_ele.count("(")):
                next_closing_pos = between_parenthesis.find(")", next_closing_pos+1)
                next_opening_pos = between_parenthesis.find("(", next_opening_pos+1)
                if next_closing_pos < next_opening_pos:
                    between_parenthesis = between_parenthesis[1:next_closing_pos]
                    break
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
    elif "\'" in key_word:
        sep = "'"
    else:
        return None
    key_word = key_word.replace(sep, "")
    if key_word:
        return ConfigElement(key_word, ele_type, line, line_nr, default_val)
    else:
        return None

def get_config_value_from_csv_line(line, line_nr):
    if line.count("\"") < 2:
        return None
    line = line.strip()
    key_word = line[line.find("\"") + 1:]
    description = key_word
    next_pos = key_word.find("\"")
    key_word = key_word[:next_pos].strip()
    description = description[next_pos + 1:]
    description = description[description.find("\"") + 1:description.rfind("\"")].strip()
    if key_word:
        return ConfigElement(key_word, None, line, line_nr, None, description)
    else:
        return None

def convert_to_list_style(list_of_config_elements, list_name):
    text = "    .. list-table:: " + list_name + "\n        :widths: 25 100 10\n        :header-rows: 1\n\n"
    text += "        * - Parameter\n          - Description\n          - Type\n"
    spacing_value = 105
    for ele in list_of_config_elements:
        text += "        * - " + ele.key_word + "\n"
        description = ele.description.strip()
        if len(description) < spacing_value:
            text += "          - " + description + "\n"
        else:
            last_pos = 0
            amount_of_splits = len(description) // spacing_value
            for i in range(amount_of_splits):
                next_split = description.rfind(" ", 0, last_pos + spacing_value)
                current_des = description[last_pos:next_split]
                last_pos = next_split + 1
                if i == 0:
                    text += "          - " + current_des + "\n"
                else:
                    text += "            " + current_des + "\n"
            if last_pos < len(description):
                current_des = description[last_pos:].strip()
                if len(current_des) > 0:
                    text += "            " + current_des + "\n"
        if text[-2] == "\"":
            text = text[:-2] + "\n"
        if ele.ele_type:
            text += "          - " + ele.ele_type + "\n"
        else:
            print("Warning: {}".format(ele.key_word))
            text += "          -\n"


    return text[:-1]

class ConfigElement(object):

    def __init__(self, key_word, ele_type, line, line_nr, default_val, description=None):
        self.key_word = key_word.strip()
        self.ele_type = ele_type
        self.default_value = default_val
        self.description = description
        if self.description and "Type:" in self.description:
            self.set_type(line)
            first_part = self.description[self.description.find("\"")+1:self.description.find("Type:")]
            self.description = first_part + \
                               self.description[self.description.rfind(self.ele_type) + len(self.ele_type)+1:]
            self.description = self.description.replace("  ", " ")
        self.line = line
        self.line_nr = line_nr
        self.found_usage = None

    def __repr__(self):
        if self.default_value:
            return str("{}({}): {}, description: {}".format(self.key_word, self.ele_type, self.default_value, self.description))
        else:
            return str("{}({}), description: {}".format(self.key_word, self.ele_type, self.description))

    def set_type(self, line):
        if "Type:" in line:
            ele_type = line[line.find("Type:") + len("Type:"):]
            ele_type = ele_type.strip()
            if "Default" in ele_type:
                poses = [ele_type.find("Default"), ele_type.find(".Default"), ele_type.find(". Default"),
                         ele_type.find(",Default"), ele_type.find(", Default")]
            else:
                poses = [max([ele_type.find(". "), ele_type.find("."), ele_type.find(".\"")]),
                         ele_type.find(" "), ele_type.find(", ")]
            # eleminate not found
            poses = [ele for ele in poses if ele > 0]
            if poses:
                end_pos = min(poses)
                ele_type = ele_type[:end_pos]
            if ele_type:
                self.ele_type = ele_type

    def add_description(self, line):
        if line.count("\"") < 2:
            return
        line = line.strip()
        if "Type:" in line:
            self.set_type(line)
            first_part = line[line.find("\"")+1:line.find("Type:")]
            line = first_part + line[line.rfind(self.ele_type) + len(self.ele_type)+1:]
        else:
            line = line[line.find("\"")+1: line.rfind("\"")].strip()
        self.description = self.description + " " + line
        self.description = self.description.replace("  ", " ")

    def set_default(self, line):
        if "Default:" in line:
            default_val = line[line.find("Default:") + len("Default:"):]
            default_val = default_val.strip()
            float_mode = default_val[0].isnumeric()
            list_mode = default_val[0] == "["
            end_pos = -1
            first_point = True
            if float_mode or list_mode:
                for index, ele in enumerate(default_val):
                    end_pos = index
                    if float_mode and ele.isnumeric():
                        continue
                    if float_mode and ele == "." and first_point:
                        first_point = False
                        continue
                    elif float_mode:
                        break
                    elif list_mode and ele == "]":
                        end_pos += 1
                        break
            else:
                poses = [max([default_val.find(". "), default_val.find("."), default_val.find(".\"")]),
                         default_val.find("\""), default_val.find(" "), default_val.find(", ")]
                poses = [ele for ele in poses if ele > 0]
                if poses:
                    end_pos = min(poses)
            if end_pos != -1:
                default_val = default_val[:end_pos]
            if default_val:
                self.default_value = default_val

def convert_element_to_type(element, ele_type):
    convert_str = "{}({})".format(ele_type, element)
    return eval(convert_str)


def check_if_element_is_of_type(element, ele_type):
    try:
        convert_str = "{}({})".format(ele_type, element)
        eval(convert_str)
    except ValueError:
        return False
    except NameError:
        return False
    except TypeError:
        return False
    except SyntaxError as e:
        print(convert_str, ele_type, element)
        raise e
    return True

def check_if_element_is_correct(current_element):
    errors = []
    if current_element.ele_type is None:
        if current_element.found_usage:
            errors.append(
                "This key '{}' does not have a Type, used type in code: {}".format(current_element.key_word,
                                                                                   [ele.ele_type for ele in
                                                                                    current_element.found_usage]))
        else:
            errors.append("This key '{}' does not have a Type".format(current_element.key_word))
    if current_element.default_value and current_element.found_usage:
        for found_value in current_element.found_usage:
            f_default_v = found_value.default_value
            if f_default_v != current_element.default_value:
                ele_type = current_element.ele_type.lower()
                if ele_type == "int" or ele_type == "float":
                    current_def_val = current_element.default_value
                    if check_if_element_is_of_type(f_default_v, found_value.ele_type) and \
                       check_if_element_is_of_type(current_def_val, current_element.ele_type):
                        found_val = convert_element_to_type(f_default_v, found_value.ele_type)
                        current_val = convert_element_to_type(current_def_val, current_element.ele_type)
                        if found_val != current_val:
                            errors.append("The default value does not match the value in the docu for key: {} "
                                          "({}!={})".format(current_element.key_word,
                                                            current_element.default_value, found_value.default_value))

    elif current_element.found_usage:
        for found_value in current_element.found_usage:
            if check_if_element_is_of_type(found_value.default_value, found_value.ele_type):
                errors.append("The key '{}' misses the default value used in "
                              "the code: {}".format(current_element.key_word, found_value.default_value))

    return errors


if __name__ == "__main__":

    parser = argparse.ArgumentParser("Finds missing documentation in BlenderProc")
    parser.add_argument("-s", "--src", help="You can specify a certain source folder to see only modules "
                                            "from this folder", type=str)
    args = parser.parse_args()

    exempt_files = ["Utility.py"]

    all_py_files = find_all_py_files(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "blenderproc"))
    for py_file in all_py_files:
        base_name = os.path.basename(py_file)
        if args.src and args.src not in py_file:
            continue
        skip_this_file = False
        for exempt_file in exempt_files:
            if exempt_file in base_name:
                skip_this_file = True
        if skip_this_file:
            continue
        if "scripts" not in os.path.abspath(py_file):
            with open(py_file, "r") as file:
                errors = []
                lines = file.read().split("\n")
                list_of_splits = []
                notDone = True
                last_start_lines = 0
                while notDone:
                    notDone = False
                    found_config_values = []
                    start_csv_table = False
                    line_nr_span = [-1, -1]
                    for line_nr, line in enumerate(lines[last_start_lines:]):
                        current_line_nr = line_nr + last_start_lines
                        if "csv-table" in line and not start_csv_table:
                            start_csv_table = True
                            line_nr_span[0] = current_line_nr
                        elif (line.strip().startswith("**") or "csv-table" in line \
                                or '"""' in line) and start_csv_table:
                            line_nr_span[1] = current_line_nr
                            last_start_lines = current_line_nr
                            notDone = True
                            break
                        elif start_csv_table and "__init__" in line:
                            break
                        if start_csv_table:
                            line = line.strip()
                            org_line = line
                            first_mark = line.find('"')
                            second_mark = line.find('"', first_mark + 1)
                            space_pos = line.find(" ")
                            available = line.find("Available:")
                            if line and "\", \"" in line and not ":header:" in line and \
                                    (space_pos > second_mark and (available != -1 and space_pos < available or available == -1) ):
                                config_element = get_config_value_from_csv_line(line, current_line_nr)
                                if config_element:
                                    found_config_values.append(config_element)
                            elif "\"" in line and not ":header" in line:
                                found_config_values[-1].add_description(line)
                    if line_nr_span[0] > 0:
                        list_of_splits.append((line_nr_span, found_config_values))

            last_used = 0
            final_text = []
            for line_nr_span, found_config_values in list_of_splits:
                final_text.extend(lines[last_used:line_nr_span[0]])
                final_text.extend(convert_to_list_style(found_config_values, "").split("\n"))
                last_used = line_nr_span[1]
            final_text.extend(lines[last_used:])
            final_text = "\n".join(final_text)
            final_text.replace("\n\n", "\n")

            with open(py_file, "w") as file:
                file.write(final_text)






