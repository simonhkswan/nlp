# -*- coding: utf-8 -8-
"""This module contains layer classes that can be used to build neural models.

Layers:
    * BaseLayer
    * FullyConnected
    * BiLSTM
    * Attention
    * Reshape

"""
from abc import ABC, abstractmethod


class BaseLayer(ABC):
    """The abstract base layer class for all Layers."""
    def __init__(self, layer_name):
        """Initialises the BaseLayer class.

        Args:
            layer_name (str): Name used to recognise the layer in json data.
        """
        self.layer_name = layer_name

    @abstractmethod
    def

    @abstractmethod
    def to_json(self):
        """Converts the layer to a json format."""
        layer = {"layer_name": self.layer_name}
        return layer

    @staticmethod
    @abstractmethod
    def from_json(json_dict):
        """Creates a layer class from json data.

        Args:
            json_dict (dict): the json dictionary containing the layer data.
        """
        pass
