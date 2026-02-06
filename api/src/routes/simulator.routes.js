const express = require('express');
const router = express.Router();
const mqttService = require('../services/mqtt.service');
const { validate, schemas } = require('../middleware/validation');
const logger = require('../utils/logger');

/**
 * POST /api/simulator/start
 * Start publishing sensor data for specific production lines
 */
router.post('/start', validate(schemas.simulatorControl), async (req, res, next) => {
  try {
    const { production_lines } = req.validatedBody;

    const result = await mqttService.startProductionLines(production_lines);

    logger.info(`Started publishing for ${production_lines.length} production lines: ${production_lines.join(', ')}`);

    res.status(200).json({
      status: 'success',
      message: `Started publishing for ${production_lines.length} production line(s)`,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/simulator/stop
 * Stop publishing sensor data for specific production lines
 */
router.post('/stop', validate(schemas.simulatorControl), async (req, res, next) => {
  try {
    const { production_lines } = req.validatedBody;

    const result = await mqttService.stopProductionLines(production_lines);

    logger.info(`Stopped publishing for ${production_lines.length} production lines: ${production_lines.join(', ')}`);

    res.status(200).json({
      status: 'success',
      message: `Stopped publishing for ${production_lines.length} production line(s)`,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/simulator/status
 * Get current simulator status (active production lines)
 */
router.get('/status', (req, res) => {
  const status = mqttService.getSimulatorStatus();

  res.status(200).json({
    status: 'success',
    data: status
  });
});

/**
 * GET /api/simulator/config
 * Get simulator configuration (production lines and sensors)
 */
router.get('/config', async (req, res, next) => {
  try {
    let config = mqttService.getSimulatorConfig();

    // If config not available, request it from the simulator
    if (!config) {
      logger.info('Config not available, requesting from simulator...');
      await mqttService.requestSimulatorConfig();

      // Wait a bit for the response
      await new Promise(resolve => setTimeout(resolve, 500));

      config = mqttService.getSimulatorConfig();

      if (!config) {
        return res.status(404).json({
          status: 'error',
          message: 'Simulator configuration not available. Ensure the simulator is running and connected to MQTT.'
        });
      }
    }

    res.status(200).json({
      status: 'success',
      data: config
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
