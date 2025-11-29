# sync-docker-images-to-acr

A GitHub Actions-based solution for automatically syncing Docker images to Alibaba Cloud Container Registry (ACR) with tag filtering capabilities. The image synchronization capability is powered by [image-syncer](https://github.com/AliyunContainerService/image-syncer).

## Features

- 📦 **Hierarchical Grouping**: Organize sync configurations into structured groups (e.g., frontend, backend, etc.)
- 🏷️ **Flexible Tag Select**: Scan and filter images by regex patterns, version ranges, and limits
- 🚀 **Parallel Execution**: Concurrent syncing of multiple business units using GitHub Actions matrix strategy
- 🧩 **Extensible Registry Support**: Designed to support additional Docker registries with minimal changes

## Quick Start

1. **Fork this repository**

2. **Configure GitHub Secrets** (Settings → Secrets and variables → Actions):
   - `DOCKER_HUB_USERNAME`: Docker Hub username
   - `DOCKER_HUB_PASSWORD`: Docker Hub password or access token
   - `ALIYUN_ACR_USERNAME`: Alibaba Cloud ACR username
   - `ALIYUN_ACR_PASSWORD`: Alibaba Cloud ACR password

3. **Create image templates** in `image_templates/` directory (see Template Syntax below)

4. **Configure workflow matrix** in `.github/workflows/scan-and-sync-image.yml`:
   ```yaml
   strategy:
     matrix:
       target:
         - app
         - db
   ```

5. **Trigger workflow**: Default runs automatically every Monday, or manually via `workflow_dispatch`
   ```yaml
    on:
      schedule:
        - cron: '0 0 * * 1'
      workflow_dispatch:
   ```


## Template Syntax

Create YAML files in `image_templates/` directory. Each file contains a list of image configurations:


| Field | Required | Description |
|-------|----------|-------------|
| `image` | Yes | Source image name (e.g., `"mongo"` or `"user/mongo"`) |
| `mirror_image` | Yes | Target ACR registry path(s) |
| `registry` | No | Source registry (default: `docker.io`) |
| `versions` | No | List of regex patterns to match tags |
| `min_version` | No | Minimum version filter |
| `max_version` | No | Maximum version filter |
| `limit` | No | Maximum number of matching tags to sync |


### Template Examples

**Sync specific versions:** Sync `redis` version tag `6.2` and `7.4`.
```yaml
- image: "redis"
  mirror_image: 
    - "registry.cn-shanghai.aliyuncs.com/namespace/mongo"
  versions: 
    - "^6.2$"
    - "^7.4$"
  min_version: ""
  max_version: ""
  limit: 10
```

**Sync version range:** Sync `mongo` version from `7.2` with postfix `-alpine` and version `8.0`.
```yaml
- image: "mongo"
  mirror_image: 
    - "registry.cn-shanghai.aliyuncs.com/namespace/mongo"
  versions: 
    - "^8.0$"
    - "^[0-9.]+$\\-alpine"
  min_version: "7.2"
  max_version: ""
  limit: 10
```