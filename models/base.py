from abc import ABC, abstractmethod


class Model(ABC):
    def __init__(self, in_type, out_type, feature_extractor, **kwargs):
        self.in_type = in_type
        self.out_type = out_type
        self.fe = feature_extractor

    @abstractmethod
    def predict(self, x):
        pass

    @abstractmethod
    def to_json(self):
        model = {
            "metadata": {
                "in_type": self.in_type,
                "out_type": self.out_type
            },
            "feature_extractor": self.fe.to_json()
        }
        return model

    @staticmethod
    @abstractmethod
    def from_json(json_dict):
        # in_type = json_dict["metadata"]["in_type"]
        # out_type = json_dict["metadata"]["out_type"]
        # fe = fe_from_dict(json_dict["feature_extractor"])
        pass
