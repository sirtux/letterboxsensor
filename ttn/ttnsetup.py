import random
import urllib

import click
import requests
import logging

logger = logging.getLogger(__name__)


def hexify(input):
    output = ""
    for byte in input:
        output = output + f"0x{byte:02x}, "
    return output


def get_applications(headers):

    url = "https://eu1.cloud.thethings.network/api/v3/applications"
    apps = requests.get(url, headers=headers).json()

    logger.debug(f"Got {len(apps)} applications")
    logger.debug(f"Applications: {apps}")

    return apps


def set_formatter(headers, appname):
    url = f"https://eu1.cloud.thethings.network/api/v3/as/applications/{appname}/link"
    data = {
        "link": {
            "default_formatters": {
                "down_formatter": "FORMATTER_NONE",
                "down_formatter_parameter": "",
                "up_formatter": "FORMATTER_JAVASCRIPT",
                "up_formatter_parameter": "function decodeUplink(input) {\n  // Decode an uplink message from a buffer\n  // (array) of bytes to an object of fields.\n  var decoded = {};\n\n  decoded.bytes = input.bytes;\n\n  decoded.voltage = 1.17 / ((((input.bytes[2]<<8)>>>0) + input.bytes[1]) / 4095);\n  decoded.sensor1 = ((input.bytes[4]<<8)>>>0) + input.bytes[3];\n  decoded.sensor2 = ((input.bytes[6]<<8)>>>0) + input.bytes[5];\n  decoded.threshold = input.bytes[7];\n\n  return {\n    data: decoded,\n    warnings: [],\n    errors: []\n  };\n}",
            }
        },
        "field_mask": {
            "paths": [
                "default_formatters.down_formatter",
                "default_formatters.down_formatter_parameter",
                "default_formatters.up_formatter",
                "default_formatters.up_formatter_parameter",
            ]
        },
    }

    result = requests.put(url, headers=headers, json=data)
    logger.debug(f"Got Status Code: {result.status_code}, Content: {result.json()}")
    if result.status_code != 200:
        raise Exception(f"Error during formater setup: {result.json()}")
    logger.info("Set up the formatter")


def create_app(headers, appname, org):
    data = {
        "application": {
            "application_server_address": "eu1.cloud.thethings.network",
            "description": "Letterbox Application",
            "name": appname,
            "join_server_address": "eu1.cloud.thethings.network",
            "network_server_address": "eu1.cloud.thethings.network",
            "ids": {"application_id": appname},
        }
    }

    url = f"https://eu1.cloud.thethings.network/api/v3/users/{org}/applications"

    result = requests.post(url, headers=headers, json=data)
    logger.debug(f"Got Status Code: {result.status_code}, Content: {result.json()}")
    if result.status_code != 200:
        raise Exception(f"Error during application creation: {result.json()}")
    logger.info("Application created")


@click.group()
@click.option("--ttntoken", help="Your ttn token", envvar="TTNTOKEN")
@click.option("--appname", help="Name of your app", default="WB-LetterBoxSensor")
@click.option("--org", help="TTN Organization", envvar="TTNORG")
@click.option("--verbose", help="Enable debugging", default=True)
@click.pass_context
def cli(ctx, ttntoken, appname, verbose, org):
    ctx.ensure_object(dict)
    ctx.obj["ttntoken"] = ttntoken
    ctx.obj["appname"] = appname
    ctx.obj["org"] = org

    if bool(verbose):
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    logging.basicConfig(level=log_level)


@cli.command()
@click.pass_context
def setup(ctx):
    """Set up the receiver Application in TTN"""
    # Basic setup

    ttntoken = ctx.obj["ttntoken"]
    appname = ctx.obj["appname"]
    org = ctx.obj["org"]

    headers = {"Authorization": f"Bearer {ttntoken}", "Accept": "application/json"}

    # Some sanitization
    appname = urllib.parse.quote_plus(appname).lower()
    logger.debug(f"Sanitized AppName to {appname}")

    # Let's check if our application already exists
    ttn_applications = get_applications(headers)
    app_exists = False
    for app in ttn_applications["applications"]:
        if app["ids"]["application_id"] == appname:
            app_exists = True
            logger.info(f"App {appname} exists, not creating it")

    # Let's create the app
    if not app_exists:
        create_app(headers, appname, org)
        logger.info(f"App {appname} doesn't exist, creating it")

    # Set the right formatters
    set_formatter(headers, appname)


def register_device_at_ttn(headers, app_eui, dev_eui, app_key, devicename, appname):

    device_url = (
        f"https://eu1.cloud.thethings.network/api/v3/applications/{appname}/devices"
    )

    device_data = {
        "end_device": {
            "ids": {
                "join_eui": app_eui.upper(),
                "dev_eui": dev_eui.upper(),
                "device_id": devicename,
                "application_ids": {"application_id": appname},
            },
            "network_server_address": "eu1.cloud.thethings.network",
            "application_server_address": "eu1.cloud.thethings.network",
            "join_server_address": "eu1.cloud.thethings.network",
        },
        "field_mask": {
            "paths": [
                "network_server_address",
                "application_server_address",
                "join_server_address",
            ]
        },
    }

    result = requests.post(device_url, headers=headers, json=device_data)
    logger.debug(f"Got Status Code: {result.status_code}, Content: {result.json()}")
    if result.status_code != 200:
        raise Exception(f"Error during device registration setup: {result.json()}")

    device_config_url_ns = f"https://eu1.cloud.thethings.network/api/v3/ns/applications/{appname}/devices/{devicename}"
    device_config_ns = {
        "end_device": {
            "frequency_plan_id": "EU_863_870_TTN",
            "lorawan_version": "MAC_V1_0_3",
            "lorawan_phy_version": "PHY_V1_0_3_REV_A",
            "supports_join": True,
            "multicast": False,
            "supports_class_b": False,
            "supports_class_c": False,
            "mac_settings": {"rx2_data_rate_index": 0, "rx2_frequency": "869525000"},
            "ids": {
                "join_eui": app_eui.upper(),
                "dev_eui": dev_eui.upper(),
                "device_id": devicename,
                "application_ids": {"application_id": appname},
            },
        },
        "field_mask": {
            "paths": [
                "frequency_plan_id",
                "lorawan_version",
                "lorawan_phy_version",
                "supports_join",
                "multicast",
                "supports_class_b",
                "supports_class_c",
                "mac_settings.rx2_data_rate_index",
                "mac_settings.rx2_frequency",
                "ids.join_eui",
                "ids.dev_eui",
                "ids.device_id",
                "ids.application_ids.application_id",
            ]
        },
    }

    result = requests.put(device_config_url_ns, headers=headers, json=device_config_ns)
    logger.debug(f"Got Status Code: {result.status_code}, Content: {result.json()}")
    if result.status_code != 200:
        raise Exception(f"Error during device config: {result.json()}")

    device_config_url_as = f"https://eu1.cloud.thethings.network/api/v3/as/applications/{appname}/devices/{devicename}"
    device_config_as = {
        "end_device": {
            "ids": {
                "join_eui": app_eui.upper(),
                "dev_eui": dev_eui.upper(),
                "device_id": devicename,
                "application_ids": {"application_id": appname},
            }
        },
        "field_mask": {
            "paths": [
                "ids.join_eui",
                "ids.dev_eui",
                "ids.device_id",
                "ids.application_ids.application_id",
            ]
        },
    }

    result = requests.put(device_config_url_as, headers=headers, json=device_config_as)
    logger.debug(f"Got Status Code: {result.status_code}, Content: {result.json()}")
    if result.status_code != 200:
        raise Exception(f"Error during device config: {result.json()}")

    device_config_url_js = f"https://eu1.cloud.thethings.network/api/v3/js/applications/{appname}/devices/{devicename}"
    device_config_js = {
        "end_device": {
            "ids": {
                "join_eui": app_eui.upper(),
                "dev_eui": dev_eui.upper(),
                "device_id": devicename,
                "application_ids": {"application_id": appname},
            },
            "network_server_address": "eu1.cloud.thethings.network",
            "application_server_address": "eu1.cloud.thethings.network",
            "root_keys": {"app_key": {"key": app_key.upper()}},
        },
        "field_mask": {
            "paths": [
                "network_server_address",
                "application_server_address",
                "ids.join_eui",
                "ids.dev_eui",
                "ids.device_id",
                "ids.application_ids.application_id",
                "root_keys.app_key.key",
            ]
        },
    }

    result = requests.put(device_config_url_js, headers=headers, json=device_config_js)
    logger.debug(f"Got Status Code: {result.status_code}, Content: {result.json()}")
    if result.status_code != 200:
        raise Exception(f"Error during device config: {result.json()}")

    logger.info("Device added.")


@cli.command()
@click.pass_context
@click.option(
    "--devicename",
    help="Device Name",
)
def register_device(ctx, devicename):
    """Register a device to the application"""
    ttntoken = ctx.obj["ttntoken"]
    appname = urllib.parse.quote_plus(ctx.obj["appname"]).lower()

    org = ctx.obj["org"]

    app_eui = bytes.fromhex("BEEFBEEFF00DF00D")
    dev_eui = random.randbytes(8)
    app_key = random.randbytes(16)

    if devicename is None:
        devicename = dev_eui.hex()

    logger.debug(
        f"AppEUI: {app_eui.hex()}, DeviceEUI: {dev_eui.hex()}, AppKey: {app_key.hex()}, DeviceID: {devicename}"
    )

    headers = {"Authorization": f"Bearer {ttntoken}", "Accept": "application/json"}

    register_device_at_ttn(
        headers, app_eui.hex(), dev_eui.hex(), app_key.hex(), devicename, appname
    )
    print("Configure your device!")
    print(f"OTAA_DEVEUI {hexify(dev_eui)}")
    print(f"OTAA_APPEUI {hexify(app_eui)}")
    print(f"OTAA_APPKEY {hexify(app_key)}")


if __name__ == "__main__":
    cli(obj={})
