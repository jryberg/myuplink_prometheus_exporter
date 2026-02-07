# myuplink_prometheus_exporter
Connect to myUplink and export metrics to Prometheus

Supports myUplink connected devices from Nibe, Cetetherm, ClimateMaster, Contura, CTA, Enertech, CTC, Hoiax, IEC (International Environmental) such as Nibe S-series heat pumps

## Prerequisites

1. A free myUplink account. Create an account, or use an existing myUplink account, and log in at [api.myuplink.com](https://api.myuplink.com)
2. You can only get data from your own equipment. Ensure that the account used has active devices. Log in at [myUplink](https://myuplink.com) to verify.

## Getting your API credentials

1. Go to [Apps](https://api.myuplink.com/apps) and create an app as described in the documentation under "Client Registration".
2. Note the **Client Identity** and **Client Secret** from the created app.
3. To verify your credentials work, go to [Swagger](https://api.myuplink.com/swagger) and click the green "Authorize" button. Enter your Client Identity and Client Secret, click Authorize, then Close. The padlock icons should now show as locked.
4. Scroll down to **GET /v2/systems/me**, click "Try it out", then "Execute" to confirm you get a response with your systems.

## Configuration

The exporter is configured using environment variables. When using docker-compose, create a `.env` file in the same directory as `docker-compose.yaml`:

```
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here
```

Replace the values with the Client Identity and Client Secret from your myUplink app.

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `client_id` | Yes | | OAuth2 Client Identity from myUplink |
| `client_secret` | Yes | | OAuth2 Client Secret from myUplink |
| `port` | No | `5000` | Prometheus metrics listen port |
| `base_url` | No | `https://api.myuplink.com` | myUplink API base URL |
| `debug` | No | `False` | Enable debug logging |

## Running with docker-compose

```bash
docker compose up -d
```

Metrics will be available at `http://localhost:8000/metrics`.
