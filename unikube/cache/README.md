# Cache/Storage Structure

All data saved by the CLI is located in `CLI_UNIKUBE_DIRECTORY` and structured as follows:

```text
<CLI_UNIKUBE_DIRECTORY>
- cache.json
- user
  - <USER-ID>
    - info.json
    - settings.json
    - cache
      - context.json
      - IDs.json

- cluster
  - <PROJECT-ID>
    - k3d
    - remote
```

- `cache.json`: This file is the primary cache and will be loaded by the ClickContext. It contains essential information such as user authentication.

## User/Cluster Split

- `user` folder: This folder contains `<USER-ID>` folders, which contain user specific information.
- `cluster` folder: This folder contains `<PROJECT-ID>` folders, which contain project specific cluster information.

## User Files

- `info.json`: Information about the user.
- `settings.json`: User settings.
- `cache.json`: User specific caches.
