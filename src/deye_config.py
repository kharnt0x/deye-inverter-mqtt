# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os
import ssl
import sys

LOG_DEST_STDOUT = "STDOUT"
LOG_DEST_STDERR = "STDERR"


class DeyeEnv:
    @staticmethod
    def integer(env_var_name: str, default_value: int = None) -> int:
        value = os.getenv(env_var_name)
        if value:
            try:
                return int(value)
            except Exception:
                raise TypeError(f"Environment variable '{env_var_name}' is not a valid integer")
        elif default_value is not None:
            return default_value
        else:
            raise KeyError(f"Required environment variable '{env_var_name}' is not set")

    @staticmethod
    def boolean(env_var_name: str, default_value: bool = None) -> bool:
        value = os.getenv(env_var_name)
        if value and value == "true":
            return True
        elif value and value == "false":
            return False
        elif value:
            raise TypeError(
                f"Environment variable '{env_var_name}' is not a valid boolean. Must be either 'true' or 'false'"
            )
        elif default_value is not None:
            return default_value
        else:
            raise KeyError(f"Required environment variable '{env_var_name}' is not set")

    @staticmethod
    def string(env_var_name: str, default_value: str = None) -> str | None:
        value = os.getenv(env_var_name)
        if value:
            return value
        elif default_value is not None:
            return default_value
        else:
            raise KeyError(f"Required environment variable '{env_var_name}' is not set")


class DeyeMqttTlsConfig:
    def __init__(
        self,
        enabled: bool = False,
        ca_cert_path: str = "",
        client_cert_path: str = "",
        client_key_path: str = "",
        tls_version=ssl.PROTOCOL_TLSv1_2,
        insecure=False,
    ):
        self.enabled = enabled
        self.__ca_cert_path = ca_cert_path
        self.__client_cert_path = client_cert_path
        self.__client_key_path = client_key_path
        ssl.TLSVersion = tls_version
        self.insecure = insecure

    @property
    def ca_cert_path(self) -> str | None:
        return self.__ca_cert_path if self.__ca_cert_path else None

    @property
    def client_cert_path(self) -> str | None:
        return self.__client_cert_path if self.__client_cert_path else None

    @property
    def client_key_path(self) -> str | None:
        return self.__client_key_path if self.__client_key_path else None

    @staticmethod
    def from_env():
        return DeyeMqttTlsConfig(
            enabled=DeyeEnv.boolean("MQTT_TLS_ENABLED", False),
            ca_cert_path=DeyeEnv.string("MQTT_TLS_CA_CERT_PATH", ""),
            client_cert_path=DeyeEnv.string("MQTT_TLS_CLIENT_CERT_PATH", ""),
            client_key_path=DeyeEnv.string("MQTT_TLS_CLIENT_KEY_PATH", ""),
            insecure=DeyeEnv.boolean("MQTT_TLS_INSECURE", False),
        )


class DeyeMqttConfig:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        topic_prefix: str,
        availability_topic: str = "status",
        logger_status_topic: str = "logger_status",
        tls=DeyeMqttTlsConfig(),
    ):
        self.host = host
        self.port = port
        self.__username = username
        self.__password = password
        self.topic_prefix = topic_prefix
        self.availability_topic = availability_topic
        self.logger_status_topic = logger_status_topic
        self.tls = tls

    @property
    def username(self) -> str | None:
        return self.__username if self.__username else None

    @property
    def password(self) -> str | None:
        return self.__password if self.__password else None

    @staticmethod
    def from_env():
        return DeyeMqttConfig(
            host=DeyeEnv.string("MQTT_HOST"),
            port=DeyeEnv.integer("MQTT_PORT", 1883),
            username=DeyeEnv.string("MQTT_USERNAME", ""),
            password=DeyeEnv.string("MQTT_PASSWORD", ""),
            topic_prefix=DeyeEnv.string("MQTT_TOPIC_PREFIX", "deye"),
            availability_topic=DeyeEnv.string("MQTT_AVAILABILITY_TOPIC", "status"),
            logger_status_topic=DeyeEnv.string("MQTT_LOGGER_STATUS_TOPIC", "logger_status"),
            tls=DeyeMqttTlsConfig.from_env(),
        )


class DeyeLoggerConfig:
    """
    Logger is a device that connects the Solar Inverter with the internet.

    Logger is identified by a unique serial number. It is required when communicating
    with the device.
    """

    def __init__(self, serial_number: int, ip_address: str, port: int, protocol: str = "tcp"):
        self.serial_number = serial_number
        self.ip_address = ip_address
        if protocol not in ["tcp", "at"]:
            raise Exception(f"Unsupported protocol {protocol}")
        self.protocol = protocol
        if port == 0 and protocol == "tcp":
            self.port = 8899
        elif port == 0 and protocol == "at":
            self.port = 48899
        else:
            self.port = port

    @staticmethod
    def from_env():
        return DeyeLoggerConfig(
            serial_number=DeyeEnv.integer("DEYE_LOGGER_SERIAL_NUMBER"),
            ip_address=DeyeEnv.string("DEYE_LOGGER_IP_ADDRESS"),
            port=DeyeEnv.integer("DEYE_LOGGER_PORT", 0),
            protocol=DeyeEnv.string("DEYE_LOGGER_PROTOCOL", "tcp"),
        )


class DeyeConfig:
    def __init__(
        self,
        logger_config: DeyeLoggerConfig,
        mqtt: DeyeMqttConfig,
        log_level="INFO",
        log_stream=LOG_DEST_STDOUT,
        data_read_inverval=60,
        publish_on_change=False,
        event_expiry=360,
        metric_groups: [str] = [],
        active_processors: [str] = [],
        active_command_handlers: [str] = [],
        plugins_dir: str = "",
    ):
        self.logger = logger_config
        self.mqtt = mqtt
        self.log_level = log_level
        self.log_stream = log_stream
        self.data_read_inverval = data_read_inverval
        self.publish_on_change = publish_on_change
        self.event_expiry = event_expiry
        self.metric_groups = metric_groups
        self.active_processors = active_processors
        self.active_command_handlers = active_command_handlers
        self.plugins_dir = plugins_dir

    @staticmethod
    def from_env():
        try:
            return DeyeConfig(
                DeyeLoggerConfig.from_env(),
                DeyeMqttConfig.from_env(),
                log_level=DeyeEnv.string("LOG_LEVEL", "INFO"),
                log_stream=DeyeEnv.string("LOG_STREAM", LOG_DEST_STDOUT),
                data_read_inverval=DeyeEnv.integer("DEYE_DATA_READ_INTERVAL", 60),
                publish_on_change=DeyeEnv.boolean("DEYE_PUBLISH_ON_CHANGE", False),
                event_expiry=DeyeEnv.integer("DEYE_PUBLISH_ON_CHANGE_MAX_INTERVAL", 360),
                metric_groups=DeyeConfig.__read_item_set(DeyeEnv.string("DEYE_METRIC_GROUPS", "")),
                active_processors=DeyeConfig.__read_active_processors(),
                active_command_handlers=DeyeConfig.__read_active_command_handlers(),
                plugins_dir=DeyeEnv.string("PLUGINS_DIR", "plugins"),
            )
        except Exception as e:
            print(e)
            sys.exit(1)

    @staticmethod
    def __read_item_set(value: str) -> set[str]:
        return set([p.strip() for p in value.split(",")])

    @staticmethod
    def __read_active_processors() -> [str]:
        active_processors = []
        if DeyeEnv.boolean("DEYE_FEATURE_MQTT_PUBLISHER", True):
            active_processors.append("mqtt_publisher")
        if DeyeEnv.boolean("DEYE_FEATURE_SET_TIME", False):
            active_processors.append("set_time")
        if DeyeEnv.boolean("DEYE_FEATURE_TIME_OF_USE", False):
            active_processors.append("time_of_use")
        return active_processors

    @staticmethod
    def __read_active_command_handlers() -> [str]:
        active_command_handlers = []
        if DeyeEnv.boolean("DEYE_FEATURE_ACTIVE_POWER_REGULATION", False):
            active_command_handlers.append("active_power_regulation")
        if DeyeEnv.boolean("DEYE_FEATURE_TIME_OF_USE", False):
            active_command_handlers.append("time_of_use")
        return active_command_handlers
