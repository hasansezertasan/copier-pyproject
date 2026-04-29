# VPN config

This directory is mounted into the `vpn` service at `/vpn`. The
[`dperson/openvpn-client`](https://hub.docker.com/r/dperson/openvpn-client)
image auto-detects an OpenVPN config file here on startup.

## Setup

1. Drop your provider's `.ovpn` file in this directory. Any filename works —
   the entrypoint picks the first `*.ovpn` it finds. If you have multiple,
   either delete the unused ones or rename the one you want to load first.

2. If the config requires credentials, create `vpn.auth` next to the `.ovpn`
   file with two lines:

   ```text
   your-username
   your-password
   ```

   Reference it from the `.ovpn` file with `auth-user-pass /vpn/vpn.auth`.

3. Start the dev container. The `devcontainer` service uses
   `network_mode: "service:vpn"`, so all traffic from the dev shell routes
   through the tunnel.

## Verify

From inside the dev container:

```bash
curl -s https://api.ipify.org
```

The IP returned should match the VPN exit node, not your local ISP.

## Notes

- Port forwards must be declared on the `vpn` service in
  `docker-compose.yml`, not on `devcontainer`. VS Code's `forwardPorts`
  still works because it attaches via `docker exec`, not the network.
- The image enables a kill-switch by default — if the tunnel drops, no
  traffic leaks to the host network.
- Files in this directory are git-ignored except this README. Never commit
  `.ovpn` files or credentials.
