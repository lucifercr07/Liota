# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------#
#  Copyright © 2015-2016 VMware, Inc. All Rights Reserved.                    #
#                                                                             #
#  Licensed under the BSD 2-Clause License (the “License”); you may not use   #
#  this file except in compliance with the License.                           #
#                                                                             #
#  The BSD 2-Clause License                                                   #
#                                                                             #
#  Redistribution and use in source and binary forms, with or without         #
#  modification, are permitted provided that the following conditions are met:#
#                                                                             #
#  - Redistributions of source code must retain the above copyright notice,   #
#      this list of conditions and the following disclaimer.                  #
#                                                                             #
#  - Redistributions in binary form must reproduce the above copyright        #
#      notice, this list of conditions and the following disclaimer in the    #
#      documentation and/or other materials provided with the distribution.   #
#                                                                             #
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"#
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE  #
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE #
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE  #
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR        #
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF       #
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS   #
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN    #
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)    #
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF     #
#  THE POSSIBILITY OF SUCH DAMAGE.                                            #
# ----------------------------------------------------------------------------#

from liota.core.package_manager import LiotaPackage
from random import randint
import time
import socket
import logging
import random

log = logging.getLogger(__name__)

dependencies = ["wavefront"]

# ---------------------------------------------------------------------------
# This is a sample application package to publish sample device stats to
# Wavefront using MQTT protocol as DCC Comms
# User defined methods

def device_metric():
    """
    This UDM randomly return values in between 0 to 999 in order to simulate device metric
    Use case specific device metric collection logic should be provided by user
    :return:
    """
    return randint(0, 999)


class PackageClass(LiotaPackage):
    def run(self, registry):
        """
        The execution function of a liota package.
        Acquires "wavefront_mqtt" and "wavefront_mqtt_edge_system" from registry then register five devices
        and publishes device metrics to the DCC
        :param registry: the instance of ResourceRegistryPerPackage of the package
        :return:
        """
        from liota.entities.devices.simulated_device import SimulatedDevice
        from liota.lib.utilities.utility import read_user_config
        from liota.entities.metrics.metric import Metric
        import copy

        # Get values from configuration file
        config_path = registry.get("package_conf")
        config = read_user_config(config_path + '/sampleProp.conf')

        # initialize and run the physical model (simulated device)
        device_simulator = SimulatedDevice(
            name=config['DeviceName'],
            entity_type="DeviceSimulated"
            )

        # Acquiring resources from registry
        wavefront = registry.get("wavefront")
        wavefront_simulated_device = wavefront.register(device_simulator)

        try:
            # Sample device Registration
            device = SimulatedDevice(socket.gethostname() + "-ChildDev")
            
            try:
                # Registering Metric for Device
                self.metrics = []
                metric_name = "Simulated-Metrics"
                metric_simulated = Metric(name=metric_name,
                                                unit=None, 
                                                interval=2,
                                                aggregation_size=1, 
                                                sampling_function=device_metric)
                
                reg_metric_simulated = wavefront.register(metric_simulated)
                wavefront.create_relationship(wavefront_simulated_device, reg_metric_simulated)
                reg_metric_simulated.start_collecting()
                self.metrics.append(reg_metric_simulated)
            
            except Exception as e:
                log.error(
                    'Exception while loading metric {0} for device {1} - {2}'.format(metric_name,
                                                                                     str(e)))
        except Exception:
                log.info("Device Registration and Metrics loading failed")
                raise

    def clean_up(self):
        """
        The clean up function of a liota package.
        Unregister Device and Stops metric collection
        :return:
        """
        # On the unload of the package the device will get unregistered and the entire history will be deleted
        # from Pulse IoT Control Center so comment the below logic if the unregsitration of the device is not required
        # to be done on the package unload
        for metric in self.metrics:
            metric.stop_collecting()
        log.info("Cleanup completed successfully")
