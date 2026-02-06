const mqtt = require('mqtt');
const logger = require('../utils/logger');
const config = require('../config/config');

class MQTTService {
  constructor() {
    this.client = null;
    this.connected = false;
    this.currentState = {
      enabled: false,
      anomalyRate: 0.1,
      sensors: ['TEMP_003', 'VIB_007'],
      lastUpdated: null
    };
    // Simulator state tracking
    this.activeProductionLines = new Set();
    this.simulatorConfig = null;  // Stores simulator configuration
  }

  connect() {
    return new Promise((resolve, reject) => {
      const { brokerHost, brokerPort, username, password, options } = config.mqtt;

      const connectionOptions = {
        ...options,
        ...(username && password && {
          username,
          password
        })
      };

      const brokerUrl = `mqtt://${brokerHost}:${brokerPort}`;
      logger.info(`Connecting to MQTT broker at ${brokerUrl}...`);

      this.client = mqtt.connect(brokerUrl, connectionOptions);

      this.client.on('connect', () => {
        this.connected = true;
        logger.info('Connected to MQTT broker');

        // Subscribe to simulator configuration topic
        this.client.subscribe('sensors/config/simulator', { qos: 1 }, (err) => {
          if (!err) {
            logger.info('Subscribed to simulator configuration topic');
          }
        });

        resolve();
      });

      this.client.on('message', (topic, message) => {
        logger.debug(`Received message on topic: ${topic}`);

        // Handle simulator configuration updates
        if (topic === 'sensors/config/simulator') {
          try {
            this.simulatorConfig = JSON.parse(message.toString());
            logger.info(`Received simulator configuration: ${this.simulatorConfig.num_production_lines} production lines`);
            logger.info(`  Production lines: ${this.simulatorConfig.production_lines.join(', ')}`);
          } catch (error) {
            logger.error(`Failed to parse simulator config: ${error.message}`);
          }
        }
      });

      this.client.on('error', (error) => {
        logger.error(`MQTT connection error: ${error.message}`);
        if (!this.connected) {
          reject(error);
        }
      });

      this.client.on('close', () => {
        this.connected = false;
        logger.warn('MQTT connection closed');
      });

      this.client.on('reconnect', () => {
        logger.info('Attempting to reconnect to MQTT broker...');
      });
    });
  }

  disconnect() {
    if (this.client) {
      this.client.end();
      this.connected = false;
      logger.info('Disconnected from MQTT broker');
    }
  }

  publishControlCommand(command, payload = {}) {
    return new Promise((resolve, reject) => {
      if (!this.connected) {
        return reject(new Error('MQTT client not connected'));
      }

      const message = {
        command,
        payload,
        timestamp: new Date().toISOString()
      };

      const topic = config.mqtt.controlTopic;

      this.client.publish(
        topic,
        JSON.stringify(message),
        { qos: 1, retain: true },
        (error) => {
          if (error) {
            logger.error(`Failed to publish command: ${error.message}`);
            reject(error);
          } else {
            logger.info(`Published command '${command}' to ${topic}`);
            resolve(message);
          }
        }
      );
    });
  }

  async startAnomaly(anomalyRate = 0.1, sensors = null) {
    const payload = {
      enabled: true,
      anomalyRate,
      ...(sensors && { sensors })
    };

    await this.publishControlCommand('start_anomaly', payload);

    this.currentState = {
      enabled: true,
      anomalyRate,
      sensors: sensors || this.currentState.sensors,
      lastUpdated: new Date().toISOString()
    };

    return this.currentState;
  }

  async stopAnomaly() {
    await this.publishControlCommand('stop_anomaly', { enabled: false });

    this.currentState = {
      ...this.currentState,
      enabled: false,
      lastUpdated: new Date().toISOString()
    };

    return this.currentState;
  }

  async updateRate(anomalyRate) {
    const payload = {
      anomalyRate,
      enabled: this.currentState.enabled
    };

    await this.publishControlCommand('update_rate', payload);

    this.currentState = {
      ...this.currentState,
      anomalyRate,
      lastUpdated: new Date().toISOString()
    };

    return this.currentState;
  }

  async resetAnomaly() {
    await this.publishControlCommand('reset_anomaly', {});

    this.currentState = {
      ...this.currentState,
      lastUpdated: new Date().toISOString()
    };

    return this.currentState;
  }

  getStatus() {
    return {
      ...this.currentState,
      mqttConnected: this.connected
    };
  }

  isConnected() {
    return this.connected;
  }

  // Simulator control methods
  async publishSimulatorCommand(command, payload = {}) {
    if (!this.connected) {
      throw new Error('MQTT client not connected');
    }

    const topic = 'sensors/control/simulator';
    const message = {
      command,
      payload,
      timestamp: new Date().toISOString()
    };

    return new Promise((resolve, reject) => {
      this.client.publish(
        topic,
        JSON.stringify(message),
        { qos: 1, retain: true },
        (error) => {
          if (error) {
            logger.error(`Failed to publish simulator command: ${error.message}`);
            reject(error);
          } else {
            logger.info(`Published simulator command '${command}' to ${topic}`);
            resolve(message);
          }
        }
      );
    });
  }

  async startProductionLines(lineIds = []) {
    const payload = { production_lines: lineIds };
    await this.publishSimulatorCommand('start', payload);

    // Update local state
    lineIds.forEach(id => this.activeProductionLines.add(id));

    return {
      active_lines: Array.from(this.activeProductionLines),
      lastUpdated: new Date().toISOString()
    };
  }

  async stopProductionLines(lineIds = []) {
    const payload = { production_lines: lineIds };
    await this.publishSimulatorCommand('stop', payload);

    // Update local state
    lineIds.forEach(id => this.activeProductionLines.delete(id));

    return {
      active_lines: Array.from(this.activeProductionLines),
      lastUpdated: new Date().toISOString()
    };
  }

  getSimulatorStatus() {
    return {
      active_lines: Array.from(this.activeProductionLines),
      mqttConnected: this.connected
    };
  }

  getSimulatorConfig() {
    return this.simulatorConfig;
  }

  async requestSimulatorConfig() {
    if (!this.connected) {
      throw new Error('MQTT client not connected');
    }

    const topic = 'sensors/control/simulator';
    const message = {
      command: 'request_config',
      payload: {},
      timestamp: new Date().toISOString()
    };

    return new Promise((resolve, reject) => {
      this.client.publish(
        topic,
        JSON.stringify(message),
        { qos: 1 },
        (error) => {
          if (error) {
            logger.error(`Failed to request simulator config: ${error.message}`);
            reject(error);
          } else {
            logger.info('Requested simulator configuration');
            resolve();
          }
        }
      );
    });
  }
}

// Singleton instance
const mqttService = new MQTTService();

module.exports = mqttService;
