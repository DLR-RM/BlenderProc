from typing import Any, Dict, Optional


class GlobalStorage(object):
    """
    The GlobalStorage has two functions:
        1. It can store data over the boundaries of modules with the add(), set() and get() functions
        2. It keeps a global config, which can be used as a fallback strategy in the case a config value is used
           in many modules, for example the "output_dir".

    To 1. you can save your own keys in the GlobalStorage to access them in a later module.
        For example you have a personal renderer or loader, which has attributes, which are independent of the scene and
        the objects so custom properties for those are not the way to go. In these instances you can use these functions.

    Here is a list of all used global_storage_keys to avoid that your key is clashing with existing keys:

    .. list-table:: 
        :widths: 25 100 10
        :header-rows: 1

        * - Parameter
          - Description
          - Type
        * - renderer_distance_end
          - This key is saved by the Renderer during distance rendering and is used in the
            StereoGlobalMatchingWriter. 
          - string
         
    Please add all new keys you create to this list.
    
    To 2. the global config is inited during the main.Initializer module, this means before that it is not possible to
    access keys from the global config, but it is possible to add keys, which can then be later accessed for that check:
    add_to_config_before_init(). It is usually not necessary that you will access the global config yourself as each
    Config checks automatically if the key is stored in the global config, if it was not defined in the current module.
    The checking order:
    Local module then the global config if both fail the default value is used, if there is none an Exception is thrown.
    """

    # holds variables which are created during the execution to get information over module boundaries
    _storage_dict: Dict[str, Any] = {}

    # defines all variables which are stored globally and are set by the config
    _global_config: Optional["Config"] = None

    # internal variables defined before the global config exists, will be copied into the global config on init
    # and then deleted, should not be used after init of the GlobalStorage
    _add_to_global_config_at_init: Dict[str, Any] = {}

    @staticmethod
    def init_global(global_config: "Config"):
        """
        Inits the global config with the given config, global_config should be of type blenderproc.python.Config

        Adds a key value pairs from add_to_global_config_at_init

        :param global_config: the config to use
        """
        GlobalStorage._global_config = global_config
        for key, value in GlobalStorage._add_to_global_config_at_init.items():
            if not GlobalStorage._global_config.has_param(key):
                GlobalStorage._global_config.data[key] = value
            else:
                raise RuntimeError("This key was already found in the global config: {} it is also used internally, "
                                   "please use another key!".format(key))

    @staticmethod
    def add_to_config_before_init(key: str, value: Any):
        """
        Adds values to the global config before the GlobalStorage was inited, these value can only be accessed
        after the GlobalStorage was inited.

        :param key: the key which is used in the global config to identify the value
        :param value: the value which can be identified over the key
        """
        if GlobalStorage._global_config is None:
            if key not in GlobalStorage._add_to_global_config_at_init:
                GlobalStorage._add_to_global_config_at_init[key] = value
            else:
                raise RuntimeError("This key: {} was added before to the list of "
                                   "add_to_global_config_at_init!".format(key))
        else:
            raise RuntimeError("This fct. should only be called before the GlobalStorage was inited!")

    @staticmethod
    def add(key: str, value: Any):
        """
        Adds a key to the GlobalStorage this is independent of the global config, this can be used to store values
        over Module boundaries. Adding only works if there is not already a key like this in the GlobalStorage.

        For example the distance renderer sets the value "distance_end" during the rendering process, a module which is
        executed afterwards can then with get() access this value.

        These values can be added before the global config was inited as they do not depend on each other.

        :param key: which is added to the GlobalStorage
        :param value: which can be accessed by this key over the get() fct.
        """
        if key not in GlobalStorage._storage_dict.keys():
            GlobalStorage._storage_dict[key] = value
        else:
            raise RuntimeError("The key: {} was already set before with this value: {}".format(key,
                                                                                               GlobalStorage._storage_dict[key]))

    @staticmethod
    def set(key: str, value: Any):
        """
        Sets a key in the GlobalStorage this is independent of the global config, this can be used to store values
        over Module boundaries. Setting always works and overwrites existing keys

        For example the distance renderer sets the value "renderer_distance_end" during the rendering process, a module
        which is executed afterwards can then with get() access this value.

        These values can be added before the global config was inited as they do not depend on each other.

        :param key: which is added to the GlobalStorage
        :param value: which can be accessed by this key over the get() fct.
        """
        GlobalStorage._storage_dict[key] = value

    @staticmethod
    def get(key: str) -> Any:
        """
        Returns a value from the GlobalStorage, please check add() and set() for more information

        :param key: for which a value is searched
        :return: value for the key
        """
        if key in GlobalStorage._storage_dict:
            return GlobalStorage._storage_dict[key]
        else:
            raise RuntimeError("The key: {} is not in the global storage!".format(key))

    @staticmethod
    def is_in_storage(key: str) -> bool:
        """
        Checks if a key is in the GlobalStorage

        :param key: for which a value is searched
        :return: True if the key is in the storage
        """
        return key in GlobalStorage._storage_dict

    @staticmethod
    def has_param(key: str) -> bool:
        """
        Checks if this key is in the global config not in the GlobalStorage!

        :param key: which should be checked
        :return: True if the key is in the global config
        """
        if GlobalStorage._global_config is not None:
            return GlobalStorage._global_config.has_param(key)
        else:
            return False

    @staticmethod
    def get_global_config() -> "Config":
        """
        Returns the global config, this function should be used with care!

        There are only a few cases where this function should be called, please read the description at the top and
        make sure you have to call this function.

        :return: the global config as a utility.Config object
        """
        if GlobalStorage._global_config is not None:
            return GlobalStorage._global_config
        else:
            raise RuntimeError("The global config was not initialized!")
