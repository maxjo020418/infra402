# Proxmox VE API Integration

This document outlines the Proxmox VE API endpoints utilized by the `x402-fastapi-example` backend and the necessary configuration/permissions.

## Configuration

The following environment variables are required in `.env`:

*   `PVE_HOST`: URL of your Proxmox server (e.g., `https://192.168.1.100:8006`).
*   `PVE_TOKEN_ID`: API Token ID (e.g., `root@pam!mytoken`).
*   `PVE_TOKEN_SECRET`: API Token Secret.
*   `PVE_NODE`: The node name where containers will be created (e.g., `pve`).
*   `PVE_STORAGE`: Storage ID for container disks (e.g., `local-lvm`).
*   `PVE_OS_TEMPLATE`: Storage path to the container template (e.g., `local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst`).
*   `PVE_ROOT_PASSWORD`: Root password (used for generating VNC tickets).
*   `PVE_VERIFY_SSL`: `true` or `false`.

## Proxmox API Endpoints Used

The backend client (`others/pve_client.py`) interacts with the following Proxmox API endpoints. Ensure your API Token has sufficient permissions (e.g., `PVEVMAdmin`, `Datastore.AllocateSpace` on the target storage).

| Method | Endpoint | Description | Used In |
| :--- | :--- | :--- | :--- |
| `GET` | `/cluster/nextid` | Fetch the next available VMID for a new container. | Lease Creation |
| `POST` | `/nodes/{node}/lxc` | Create a new LXC container. | Lease Creation |
| `POST` | `/nodes/{node}/lxc/{vmid}/status/start` | Start a stopped container. | Lease Renewal |
| `POST` | `/nodes/{node}/lxc/{vmid}/status/stop` | Stop a running container. | Lease Expiry (Worker) |
| `GET` | `/nodes/{node}/lxc/{vmid}/status/current` | Get container status (running/stopped, etc.). | Lease Renewal, Listing |
| `POST` | `/nodes/{node}/lxc/{vmid}/exec` | Execute a command inside the container. | Management |
| `POST` | `/nodes/{node}/lxc/{vmid}/vncproxy` | Create a VNC proxy tunnel. | Console Access |
| `GET` | `/nodes/{node}/tasks/{upid}/status` | Check status of an async task (create, exec, start). | Internal (Waiting) |
| `GET` | `/nodes/{node}/tasks/{upid}/log` | Retrieve logs for a task (used for `exec` output). | Management |
| `POST` | `/access/ticket` | Generate a ticket for VNC WebSocket auth. | Console Access |

## Backend API Mapping

These Proxmox operations are exposed via the following FastAPI routes:

| Backend Route | Method | Action | Proxmox Calls |
| :--- | :--- | :--- | :--- |
| `/lease/container` | `POST` | Create Lease | `nextid`, `create_lxc` |
| `/lease/{ctid}/renew` | `POST` | Renew Lease | `status/current`, `start` (if stopped) |
| `/management/exec/{ctid}` | `POST` | Run Command | `exec`, `tasks/{upid}/log` |
| `/management/console/{ctid}` | `POST` | Get Console URL | `access/ticket`, `vncproxy` |
| `/management/list` | `GET` | List User Containers | `status/current` (for each lease) |

## Permissions

To ensure smooth operation, the API Token User needs permissions to:
1.  Read cluster status (for `nextid`).
2.  Manage VMs on the specified `PVE_NODE` (Create, Start, Stop, Console, Exec).
3.  Allocate space on `PVE_STORAGE`.
