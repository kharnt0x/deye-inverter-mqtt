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
import json
import logging
import threading
import time
from typing import List, Tuple
from deye_config import DeyeConfig
from deye_mqtt import DeyeMqttClient
from deye_plugin_loader import DeyePluginContext
from deye_events import DeyeEventList, DeyeEventProcessor

from deye_sensor import Sensor
from deye_sensors import sensor_list

    
class MqttAutoConfPublisher(DeyeEventProcessor):
    def __init__(self, config: DeyeConfig, mqtt_client: DeyeMqttClient, sensor_configs: List[Tuple[str, str]]):
        self.__log = logging.getLogger(MqttAutoConfPublisher.__name__)
        self.__mqtt_client = mqtt_client
        self.config = config.logger
        self.sensor_configs = sensor_configs
        self.publish_sensors_periodically()
        # Set a timer to call this function again after 4 hours
        threading.Timer(4 * 60 * 60, self.publish_sensors_periodically).start()


    def get_id(self):
        return "mqtt_autoconf_publisher"
    

    def process(self, events: DeyeEventList):
        pass


    def publish_sensors_periodically(self):
        # Publish all sensors
        self.__log.info("(Re)sending autoconf for all sensors")
        call_again_in_seconds = 4 * 60 * 60
        # log the date and time this will next be called 
        next_call_date_time = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(time.time() + call_again_in_seconds))
        self.__log.info("Next call to publish_sensors_periodically will be at %s", next_call_date_time)
        for sensor_config in self.sensor_configs:
            self.publish_sensor(sensor_config[0], sensor_config[1])
        
        t = threading.Timer(call_again_in_seconds, self.publish_sensors_periodically)
        t.daemon = True
        t.start()



    def publish_sensor(self, topic: str, value: str):
        self.__mqtt_client.do_publish(topic, value)
        self.__log.info("Logger is %s", value)


class DeyePlugin:
    """Plugin entrypoint

    The plugin loader first instantiates DeyePlugin class, and then gets event processors from it. 
    """
    def __init__(self, plugin_context: DeyePluginContext):
        """Initializes the plugin

        Args:
            plugin_context (DeyePluginContext): provides access to core service components, e.g. config
        """
        self.config = plugin_context.config
        self.sensors = [s for s in sensor_list if s.in_any_group(self.config.metric_groups)]
        self.mqtt_client = plugin_context.mqtt_client
        sensor_configs: List[Tuple[str, str]] = list(map(self.__configure_sensor, self.sensors))
        self.publisher = MqttAutoConfPublisher(self.config, self.mqtt_client, sensor_configs)


    def get_event_processors(self) -> [DeyeEventProcessor]:
        """Provides a list of custom event processors 
        """
        return [self.publisher]
    
    def __configure_sensor(self, sensor: Sensor) -> Tuple[str, str]:
        """Create a Home Assistant MQTT auto discovery configuration for a sensor 
        """
        unique_id = f"deye_{self.config.logger.serial_number}_{sensor.mqtt_topic_suffix.replace('/', '' )}"
        mqtt_topic = f"homeassistant/sensor/{unique_id}/config"
        ha_config = {
            'device_class': f"{sensor.device_class}",
            'state_class': sensor.state_class if sensor.state_class is not None else 'measurement',
            'name': f"{sensor.name}",
            'state_topic': f"{self.config.mqtt.topic_prefix}/{sensor.mqtt_topic_suffix}",
            'unit_of_measurement': f"{sensor.unit}",
            'unique_id': f"{unique_id}",
            'expire_after': 300,
            'device': {
                'identifiers': [f"deye{self.config.logger.serial_number}"],
                'name': f"Deye {self.config.logger.serial_number}"
            }
        }
        return (mqtt_topic, json.dumps(ha_config))
        
