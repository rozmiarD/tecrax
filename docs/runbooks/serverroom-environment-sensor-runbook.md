# Server room environment sensor runbook

This runbook documents the operator-owned server room temperature and humidity
sensor integration for the Proxmox deployment. It records the deployed shape and
validation points without storing credentials, private dashboard exports or
secret material in Tecrax.

## Scope

- Host: `pve01`
- Sensor: AHT10-compatible temperature and humidity sensor
- USB bridge: FT232H with Blinka
- Collection path: local script on `pve01` exposed through Zabbix Agent 2
- Visualization path: Zabbix datasource in Grafana

The physical USB device remains attached directly to `pve01`. If the sensor or
bridge is moved, the Zabbix items will stop receiving current values until the
local host path is restored or deliberately migrated.

## Host-side baseline

The deployed host-side files are:

- `/opt/tecrax/sensors/read_aht10.py`
- `/opt/tecrax/sensors/read_aht10.sh`
- `/opt/tecrax/sensors/venv/`
- `/etc/udev/rules.d/90-tecrax-ft232h.rules`
- `/etc/zabbix/zabbix_agent2.d/tecrax-serverroom-sensor.conf`

The Zabbix Agent 2 user parameters are:

```text
tecrax.serverroom.temperature
tecrax.serverroom.humidity
```

The FT232H udev rule grants the local `zabbix` group access to the matching USB
device. This avoids running Zabbix as root and keeps the integration bounded to
the sensor bridge.

## Zabbix baseline

The Zabbix host is `pve01`.

Items:

- `Server room temperature`
- `Server room humidity`

Temperature triggers are range-based so that only the current severity band is
active for a given temperature:

- Warning: `>18C and <=20C`
- Average: `>20C and <=22C`
- High: `>22C and <=25C`
- Disaster: `>25C`

The trigger state resolves automatically when the latest collected temperature
falls outside the matching range.

## Grafana baseline

The main infrastructure dashboard includes:

- `Server room temperature`
- `Server room humidity`
- `Current problems - all active`

The environment panels use the existing Zabbix datasource. The current-problems
panel uses the Zabbix Problems panel and shows all active severities, not only
Average and above.

## Validation

Bounded validation commands:

```sh
zabbix_agent2 -t tecrax.serverroom.temperature
zabbix_agent2 -t tecrax.serverroom.humidity
```

Expected result:

- both keys return a numeric value,
- Zabbix item state is supported,
- `lastclock` is recent after a polling cycle,
- only the matching temperature severity trigger is active, if any.

## Boundaries

This runbook does not introduce a generic hardware-control connector, arbitrary
USB access, dashboard export storage or alert-routing policy. Final notification
routing remains a separate alerting and incident-management gate.
