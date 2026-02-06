const express = require('express');
const router = express.Router();
const mqttService = require('../services/mqtt.service');

/**
 * GET /health
 * Health check endpoint
 */
router.get('/', (req, res) => {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    mqtt: {
      connected: mqttService.isConnected()
    }
  };

  const statusCode = health.mqtt.connected ? 200 : 503;

  res.status(statusCode).json(health);
});

module.exports = router;
