#!/usr/bin/env python -u
# coding: utf-8

import os
import json
import yaml


config_dict = {}


def update_config_info(config_key, config_value):
    global config_dict

    config_dict[config_key] = config_value


# Deprecated, use "load_feature_config" to load yaml config
def load_default_config(config_file_path):
    global config_dict

    if not os.path.exists(config_file_path):
        raise Exception("config file '{}' don't exist".format(config_file_path))

    with open(config_file_path, 'r') as fread:
        try:
            config_dict = json.load(fread)
        except ValueError as e:
            raise Exception("config file '{}' format error: {}".format(config_file_path, e))


# Deprecated, use "save_total_feature_config_info" to save yaml config
def save_total_config_info(config_file_path):
    global config_dict

    if not os.path.exists(os.path.dirname(config_file_path)):
        os.makedirs(os.path.dirname(config_file_path))

    with open(config_file_path, 'w') as fwrite:
        json.dump(config_dict, fwrite, indent=4, sort_keys=True)


# Load YAML feature config for RTC SDK
def load_feature_config(feautre_config_path):
    global config_dict

    if not os.path.exists(feautre_config_path):
        raise Exception("feature config file '{}' don't exist".format(feautre_config_path))

    with open(feautre_config_path, 'r', encoding='utf8') as fread:
        try:
            config_dict = yaml.safe_load(fread)
        except ValueError as e:
            raise Exception("feature config file '{}' format error: {}".format(feautre_config_path, e))


# Save YAML feature config for RTC SDK
def save_total_feature_config_info(feautre_config_path):
    global config_dict

    if not os.path.exists(os.path.dirname(feautre_config_path)):
        os.makedirs(os.path.dirname(feautre_config_path))

    with open(feautre_config_path, 'w', encoding='utf8') as fwrite:
        yaml.dump(config_dict, fwrite, indent=4, sort_keys=True)

def get_total_config_info():
    global config_dict

    return config_dict
