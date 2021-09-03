import yaml
import re
import os
from enum import Enum
try:
  basestring
except NameError:
  basestring = str

class PlaceholderTypes(Enum):
    ARG = 1
    ENV = 2


class ConfigParser:
    def __init__(self, silent=False):
        """
        :param silent: If silent is True, then debug information is not printed
        """
        self.regex_per_type = {
            PlaceholderTypes.ARG: re.compile("\<args\:(\d+)\>"), # Matches <args:i> with i being the argument index
            PlaceholderTypes.ENV: re.compile("\<env\:([a-zA-Z_]+[a-zA-Z0-9_]*)\>") # Matches <env:name> with name being the env var name
        }
        self.config = None
        self.args = None
        self.placeholders = None
        self.silent = silent
        self.current_version = 3

    def parse(self, config_path, args, show_help=False, skip_arg_placeholders=False):
        """ Reads the yaml file at the given path and returns it as a cleaned dict.

        Removes all comments and replaces arguments and env variables with their corresponding values.

        :param config_path: The path to the yaml file.
        :param args: A list with the arguments which should be used for replacing <args:i> templates inside the config.
        :param show_help: If True, shows a help message which describes the placeholders that are used in the given config file. Exits the program afterwards.
        :param skip_arg_placeholders: If true, disregards filling up non environment type arguments.
        :return: The dict containing the configuration.
        """
        if not show_help:
            self.log("Parsing config '" + config_path + "'", is_info=True)
        with open(config_path, "r") as f:
            # Read in dict
            self.config = yaml.safe_load(f)
            self.args = args

            # Check if the config is up to date
            self._check_version()

            # Collect all placeholders
            self.placeholders = self._parse_placeholders_in_block(self.config)

            # Print help if required
            if show_help:
                self.log("Placeholders in the script '" + config_path + "':\n")
                self._show_help()
                exit(0)

            # Replace all placeholders with their corresponding value
            self._fill_placeholders_in_config(skip_arg_placeholders)

            self.log("Successfully finished parsing ", is_info=True)
        return self.config

    def _check_version(self):
        """ Checks if the configuration file contain a valid version number and if its up to date. """
        exception_text = None
        # Check if there is any version number in the config
        if "version" in self.config:
            version = self.config["version"]
            # Check if the version number is valid
            if isinstance(version, int):
                # Check if the version number is up to date
                if version < self.current_version:
                    exception_text = "The given configuration file might not be up to date. The version of the config is %d while the currently most recent version is %d." % (version, self.current_version)
                    if version == 2:
                        exception_text += " Since version 3 the global config was moved to the main.Initializer!"
            else:
                exception_text = "The given configuration file has an invalid version number. Cannot check if the config is still up to date."
        else:
            exception_text = "The given configuration file does not contain any version number. Cannot check if the config is still up to date."

        if exception_text is not None:
            raise Exception(exception_text)


    def _parse_placeholders_in_block(self, element, path=[]):
        """ Collects all placeholders in the given block.

        :param element: A dict / list / string which describes an element in the config block.
        :param path: A list of keys describing the path to the given block in the total config. e.q. ["modules", 0, "name"] means block = config["modules"][0]["name"]
        :return: A list of dicts, where each dict describes a placeholder
        """
        matches = []
        # If the element is a string, test if it contains a placeholder
        if isinstance(element, basestring):
            # Test for every placeholder if it matches
            for key, regex in self.regex_per_type.items():
                new_matches = regex.findall(element)
                for new_match in new_matches:
                    matches.append({
                        "type": key,
                        "match": new_match,
                        "path": path
                    })
        elif isinstance(element, dict):
            # Go through all child blocks
            for key, value in element.items():
                matches.extend(self._parse_placeholders_in_block(value, path + [key]))
        elif isinstance(element, list):
            # Go through all child blocks
            for key, value in enumerate(element):
                matches.extend(self._parse_placeholders_in_block(value, path + [key]))
        return matches

    def _show_help(self):
        """ Print out help message which describes the placeholders that are used in the given config file """
        self._print_placeholders(self.placeholders, {PlaceholderTypes.ARG: "Arguments:", PlaceholderTypes.ENV: "Environment variables:"})

    def _print_placeholders(self, placeholders, type_header):
        """ Print the give given placeholders grouped by typed and by key.

        :param placeholders: A list of dicts, where every dict describes one placeholder.
        :param type_header: A dict which maps every type to a string which will be printed in front of the list of placeholders with the type.
        """
        placeholders_per_type = {
            PlaceholderTypes.ARG: {},
            PlaceholderTypes.ENV: {},
        }

        # Group all placeholders by type and by key
        for placeholder in placeholders:
            placeholders_with_type = placeholders_per_type[placeholder["type"]]

            # Extract the key depending on the type
            if placeholder["type"] == PlaceholderTypes.ARG:
                key = int(placeholder["match"]) # Key is the argument number
            elif placeholder["type"] == PlaceholderTypes.ENV:
                key = placeholder["match"] # Key is the env var name

            # Add the placeholder to the list of placeholders with this specific key
            if key not in placeholders_with_type:
                placeholders_with_type[key] = []
            placeholders_with_type[key].append(placeholder["path"])

        # Go through all types
        for type, placeholders_with_type in sorted(placeholders_per_type.items(), key=lambda x: x[0].value):
            # If there are placeholders with this type
            if len(placeholders_with_type) > 0:
                # Log header
                self.log(type_header[type])

                # Log list the placeholders of this type
                for placeholder in sorted(placeholders_with_type.items(), key=lambda x: x[0]):
                    self.log("  " + self._form_argument_usage_string(type, str(placeholder[0]), placeholder[1]))
                self.log("")

    def _form_argument_usage_string(self, type, key, usages):
        """ Forms string containing placeholder and all its usage paths.

        e.q. <args:1>: Used in key1/key2, modules/1/name

        :param type: The type of the placeholder.
        :param key: The of the placeholder (e.q. argument index or env var name)
        :param usages: A list of path lists. Where a path list looks like ["key1", "key2"].
        :return: The final string
        """
        # Map key to text
        text = ""
        if type == PlaceholderTypes.ARG:
            text = "<args:" + key + ">"
        elif type == PlaceholderTypes.ENV:
            text = "<env:" + key + ">"

        # Map usage path lists to strings (["key1", "key2"] -> "key1/key2")
        usage_paths = []
        for usage in usages:
            usage_paths.append(self._placeholder_path_to_string(usage))

        text += ": Used in " + ", ".join(usage_paths)
        return text

    def _placeholder_path_to_string(self, path):
        """ Forms a string out of a path list.

        ["key1", "key2"] -> key1/key2

        Also inserts module names for better readability.

        :param path: A path list. e.q. ["key1", "key2"].
        :return: The path string.
        """
        # If the path goes through ["modules"][i] with i being the module index, then insert modules name for better readability
        if len(path) > 1 and path[0] == "modules" and "module" in self.config["modules"][path[1]]:
            path = path[:]
            path[1] = "(" + self.config["modules"][path[1]]["module"] + ")"

        return "/".join([str(path_segment) for path_segment in path])

    def _fill_placeholders_in_config(self, skip_arg_placeholders):
        """ Replaces all placeholders with their corresponding values """
        # Collect a list of all placeholders which could not be filled
        unfilled_placeholders = []

        # Go through all collected placeholders
        for placeholder in self.placeholders:
            if placeholder["type"] == PlaceholderTypes.ARG and (not skip_arg_placeholders): 
                arg_index = int(placeholder["match"])

                # Check if the argument has been given
                if arg_index < len(self.args):
                    # Replace placeholder by the given argument
                    self._fill_placeholder_at_path(placeholder["path"], "<args:" + str(arg_index) + ">", self.args[arg_index])
                else:
                    unfilled_placeholders.append(placeholder)

            elif placeholder["type"] == PlaceholderTypes.ENV:
                env_name = placeholder["match"]

                # Check if env var with this name exists
                if env_name in os.environ:
                    # Replace placeholder with the value of this env var
                    self._fill_placeholder_at_path(placeholder["path"], "<env:" + str(env_name) + ">", os.environ[env_name])
                else:
                    unfilled_placeholders.append(placeholder)

        # If there were placeholders that could not be filled, exit program and print error message
        if len(unfilled_placeholders) > 0:
            self.log("There was an error while parsing the config.\nThe following placeholders could not be filled:\n")
            self._print_placeholders(unfilled_placeholders, {PlaceholderTypes.ARG: "Missing arguments:", PlaceholderTypes.ENV: "Missing environment variables:"})
            raise Exception("Missing arguments")

    def _fill_placeholder_at_path(self, path, old, new):
        """ Replaces the given placeholder with the given value at the given path

        :param path: A path list which leads to the config value that contains the placeholder.
        :param old: The string to replace
        :param new: The string to replace it with
        """
        path_string = self._placeholder_path_to_string(path)

        # Walk down the config dict along the given path
        config = self.config
        while len(path) > 1:
            config = config[path[0]]
            path = path[1:]

        # Replace the placeholder
        config[path[0]] = config[path[0]].replace(old, new)

        self.log("Filling placeholder " + old + " at " + path_string + ": " + config[path[0]], is_info=True)

    def log(self, message, is_info=False):
        """ Prints the given message.

        :param message: The message string.
        :param is_info: True, if this message is only debug information.
        """
        # If silent is True, then debug information is not printed.
        if not is_info or not self.silent:
            print(message)
