require('dotenv').config();

module.exports = {
  server: {
    port: process.env.PORT || 3000,
    env: process.env.NODE_ENV || 'development'
  },
  mqtt: {
    brokerHost: process.env.MQTT_BROKER_HOST || 'localhost',
    brokerPort: parseInt(process.env.MQTT_BROKER_PORT) || 1883,
    username: process.env.MQTT_USERNAME || null,
    password: process.env.MQTT_PASSWORD || null,
    controlTopic: process.env.MQTT_CONTROL_TOPIC || 'sensors/control/anomaly',
    options: {
      clientId: 'anomaly_control_api',
      clean: true,
      connectTimeout: 4000,
      reconnectPeriod: 1000
    }
  }
};
