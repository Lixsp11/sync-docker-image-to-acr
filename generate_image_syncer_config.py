#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import distutils.version
import logging
import re
import time
from typing import Optional, Tuple

import requests
import yaml

ALLOWED_REGISTRYS = ["docker.io"]
REGISTRY2TAG_API_FORMAT = {
    "docker.io": "https://hub.docker.com/v2/namespaces/{namespace}/repositories/{repository}/tags"
}
REGISTRY2DEFALUT_NAMESPACE = {"docker.io": "library"}

logger = logging.getLogger(__name__)


def get_format_repository_path(image: str, registry: str) -> Tuple[str, str, str]:
    if image.count("/") == 0:
        return REGISTRY2DEFALUT_NAMESPACE[registry], image
    elif image.count("/") == 1:
        return image.split("/")
    else:
        raise RuntimeError(f"Unknown type of image '{image}'.")


def request_registry_with_retry(url, *args, **kwargs) -> Optional[requests.Response]:
    for attempt in range(1, 6):
        try:
            logging.debug(f"Request {url} ...")
            response = requests.get(url, *args, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt == 5:
                raise e
            logging.warning("Request fail with {}".format(repr(e).replace("\n", "")))
            time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scan Docker Hub based on YAML template and output image-syncer configuration."
    )
    parser.add_argument("-i", "--template_file", required=True)
    parser.add_argument("-o", "--output_file", required=True)
    parser.add_argument("-l", "--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level.upper(),
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    with open(args.template_file, "r", encoding="utf-8") as f:
        images = yaml.safe_load(f)

    image_syncer_config = {}
    for image in images:
        registry = image.get("registry", "docker.io")
        assert registry in ALLOWED_REGISTRYS, f"Registry {registry} not in ALLOWED_REGISTRYS."
        namespace, repository = get_format_repository_path(image["image"], registry)

        url = REGISTRY2TAG_API_FORMAT[registry].format(registry=registry, namespace=namespace, repository=repository)
        params = {"page_size": 100}

        tags = []
        while len(tags) < image.get("limit", float("inf")):
            if not url:
                break
            response = request_registry_with_retry(url, params=params, timeout=10).json()

            for result in response["results"]:
                flag = True
                version = distutils.version.LooseVersion(result["name"])

                if len(image.get("versions", [])) > 0 and not any(
                    re.fullmatch(pattern, version.vstring) for pattern in image["versions"]
                ):
                    flag = False
                if flag and image.get("min_version") and version < distutils.version.LooseVersion(image["min_version"]):
                    flag = False
                if flag and image.get("max_version") and version > distutils.version.LooseVersion(image["max_version"]):
                    flag = False

                if flag:
                    tags.append(version)

            url = response["next"]

        tags = [tag.vstring for tag in sorted(tags, reverse=True)][: image.get("limit", ...)]
        if len(image.get("mirror_image", [])) > 0:
            image_syncer_config[f"{registry}/{namespace}/{repository}:{','.join(tags)}"] = image["mirror_image"]
        logging.info(f"Scan {len(tags)} of {namespace}/{repository}.")

    with open(args.output_file, "w") as f:
        yaml.safe_dump(image_syncer_config, f)
