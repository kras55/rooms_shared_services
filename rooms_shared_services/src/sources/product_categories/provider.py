import os

import boto3
import yaml

from rooms_shared_services.src.settings.product_categories import Settings as ProductCategorySettings

script_dir = os.path.dirname(__file__)

CATEGORIES_PATH = "{}/categories.yml".format(script_dir)


class CategoryProvider(object):
    def __init__(self):
        """Set attributes."""
        self._settings = ProductCategorySettings()
        self.cat_list = []
        self.validated_cat_list = []
        self.cat_names = []
        self.not_allowed = [" "]
        self.root = ["categories"]
        self.s3_client = boto3.client("s3", region_name=self._settings.region_name)

    def __call__(self):
        self.provide_category_list()
        self.validate_cat_pairs()
        return self.validated_cat_list

    def load_source(self):
        s3_obj = self.s3_client.get_object(
            Bucket=self._settings.source_data_bucket,
            Key=self._settings.source_data_object,
        )
        return yaml.load(stream=s3_obj["Body"], Loader=yaml.Loader)  # noqa: S506

    def get_product_categories(self):
        with open(CATEGORIES_PATH, "r") as stream:
            return yaml.load(stream=stream, Loader=yaml.Loader)  # noqa: S506

    def provide_category_list(self):
        raw_cats = self.load_source()
        self.collect_cat_pairs(raw_cats)

    def collect_cat_pairs(self, raw_cats: dict):
        for parent, cat in raw_cats.items():
            match cat:
                case str():
                    self.cat_list.append((cat, parent))
                case dict():
                    for cat_key, _ in cat.items():
                        self.cat_list.append((cat_key, parent))  # noqa: WPS220
                    self.collect_cat_pairs(raw_cats=cat)
                case list():
                    for cat_name in cat:
                        self.cat_list.append((cat_name, parent))  # noqa: WPS220

    def validate_root(self, cat_elem: str):
        if cat_elem in self.root:
            return None
        return cat_elem

    def validate_cat_pairs(self):  # noqa: WPS231
        for cat_item in self.cat_list:
            for name in cat_item:
                for snippet in self.not_allowed:
                    if snippet in name:
                        raise ValueError("Not allowed snippet {} in {}".format(snippet, name))  # noqa: WPS220
            cat_child, cat_parent = cat_item
            if cat_child == "other":
                cat_child = "other_{}".format(cat_parent)
            if cat_child in self.cat_names:
                raise ValueError("Duplicated category name: {}".format(cat_child))
            self.cat_names.append(cat_child)
            new_cat_item = [self.validate_root(cat_elem) for cat_elem in (cat_child, cat_parent)]
            if new_cat_item != [None, None]:
                self.validated_cat_list.append((new_cat_item[0], new_cat_item[1]))
