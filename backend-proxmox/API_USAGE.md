# API Usage Guide

This guide explains how to interact with the system. There are two ways to control the infrastructure:
1.  **Backend API (Recommended):** The public-facing API that handles payments (`x402`) and manages leases.
2.  **Proxmox VE API (Direct):** Direct access to the Proxmox server for debugging or administration (requires internal credentials).

---

## 1. Backend API (x402 Payment Enabled)

The backend API is protected by the `x402` protocol. You cannot call these endpoints directly without a valid payment signature.

**Flow:**
1.  Request an endpoint (e.g., `POST /lease/container`).
2.  Receive `402 Payment Required` with payment details (price, address).
3.  Sign the payment request using a compatible wallet/client.
4.  Resend the request with the `X-PAYMENT` header containing the signed payload.

### Endpoints

#### Create Lease
**POST** `/lease/container`

Provisions a new LXC container.

**Body:**
```json
{
  "sku": "standard-lxc",
  "runtimeMinutes": 60,
  "hostname": "demo-server",
  "cores": 1,
  "memoryMB": 512,
  "diskGB": 8,
  "password": "root_password_here"
}
```

#### Renew Lease
**POST** `/lease/{ctid}/renew`

Extends the runtime of an active container.

**Body:**
```json
{
  "runtimeMinutes": 30
}
```

#### Execute Command
**POST** `/management/exec/{ctid}`

Runs a shell command inside the container.

**Body:**
```json
{
  "command": "uptime",
  "extraArgs": ["-p"]
}
```

#### Get Console
**POST** `/management/console/{ctid}`

Retrieves a VNC ticket and connection details.

Notes:
- The returned `consoleUrl` is time-sensitive (VNC tickets expire quickly); open it right away.
- `PVE_CONSOLE_HOST` should be the host users can reach in their browser (it may differ from `PVE_HOST`, which is used for backend API calls).

**Body:**
```json
{
  "consoleType": "vnc"
}
```

#### List Containers
**GET** `/management/list`

Lists all active leases for the authenticated user.

---

## 2. Proxmox VE API (Direct Access)

For debugging or manual intervention, you can hit the Proxmox API directly using the credentials found in your `.env` file.

**Prerequisites:**
*   `PVE_HOST`: e.g., `https://192.168.1.100:8006`
*   `PVE_TOKEN_ID`: e.g., `root@pam!mytoken`
*   `PVE_TOKEN_SECRET`: e.g., `12345-67890-abcd...`

**Authentication Header:**
```bash
Authorization: PVEAPIToken=root@pam!mytoken=12345-67890-abcd...
```

### Common Operations (cURL Examples)

#### 1. Check Next Available VMID
Corresponds to `get_next_vmid` in backend.

```bash
curl -k -H "Authorization: PVEAPIToken=$PVE_TOKEN_ID=$PVE_TOKEN_SECRET" \
     "$PVE_HOST/api2/json/cluster/nextid"
```

#### 2. Create Container
Corresponds to `create_lxc`.

```bash
curl -k -X POST -H "Authorization: PVEAPIToken=$PVE_TOKEN_ID=$PVE_TOKEN_SECRET" \
     -d "vmid=105" \
     -d "ostemplate=local:vztmpl/debian-12-standard.tar.zst" \
     -d "cores=1" -d "memory=512" -d "rootfs=local-lvm:8" \
     -d "password=securepass" \
     "$PVE_HOST/api2/json/nodes/$PVE_NODE/lxc"
```

#### 3. Start Container
Corresponds to `start_lxc`.

```bash
curl -k -X POST -H "Authorization: PVEAPIToken=$PVE_TOKEN_ID=$PVE_TOKEN_SECRET" \
     "$PVE_HOST/api2/json/nodes/$PVE_NODE/lxc/105/status/start"
```

#### 4. Stop Container
Corresponds to `stop_lxc`.

```bash
curl -k -X POST -H "Authorization: PVEAPIToken=$PVE_TOKEN_ID=$PVE_TOKEN_SECRET" \
     "$PVE_HOST/api2/json/nodes/$PVE_NODE/lxc/105/status/stop"
```

#### 5. Get Container Status
Corresponds to `get_lxc_status`.

```bash
curl -k -H "Authorization: PVEAPIToken=$PVE_TOKEN_ID=$PVE_TOKEN_SECRET" \
     "$PVE_HOST/api2/json/nodes/$PVE_NODE/lxc/105/status/current"
```

#### 6. Execute Command
Corresponds to `run_command`. This is a two-step process: initiate execution, then read the log.

**Step A: Trigger Execution**
```bash
curl -k -X POST -H "Authorization: PVEAPIToken=$PVE_TOKEN_ID=$PVE_TOKEN_SECRET" \
     -d "command=ls" -d "params=-la" \
     "$PVE_HOST/api2/json/nodes/$PVE_NODE/lxc/105/exec"
# Returns a UPID (Unique Process ID)
```

**Step B: Read Output**
```bash
curl -k -H "Authorization: PVEAPIToken=$PVE_TOKEN_ID=$PVE_TOKEN_SECRET" \
     "$PVE_HOST/api2/json/nodes/$PVE_NODE/tasks/<UPID_FROM_ABOVE>/log"
```

For a complete list of used endpoints and their purpose, refer to [PROXMOX_API_USAGE.md](./PROXMOX_API_USAGE.md).
