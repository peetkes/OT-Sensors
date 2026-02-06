const express = require('express');
const router = express.Router();
const mqttService = require('../services/mqtt.service');
const { validate, schemas } = require('../middleware/validation');
const logger = require('../utils/logger');

/**
 * POST /api/anomaly/start
 * Start anomaly generation
 */
router.post('/start', validate(schemas.startAnomaly), async (req, res, next) => {
  try {
    const { anomalyRate, sensors } = req.validatedBody;

    const result = await mqttService.startAnomaly(anomalyRate, sensors);

    logger.info(`Anomaly generation started with rate: ${anomalyRate}`);

    res.status(200).json({
      status: 'success',
      message: 'Anomaly generation started',
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/anomaly/stop
 * Stop anomaly generation
 */
router.post('/stop', async (req, res, next) => {
  try {
    const result = await mqttService.stopAnomaly();

    logger.info('Anomaly generation stopped');

    res.status(200).json({
      status: 'success',
      message: 'Anomaly generation stopped',
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/anomaly/status
 * Get current anomaly generation status
 */
router.get('/status', (req, res) => {
  const status = mqttService.getStatus();

  res.status(200).json({
    status: 'success',
    data: status
  });
});

/**
 * PATCH /api/anomaly/rate
 * Update anomaly generation rate
 */
router.patch('/rate', validate(schemas.updateRate), async (req, res, next) => {
  try {
    const { anomalyRate } = req.validatedBody;

    const result = await mqttService.updateRate(anomalyRate);

    logger.info(`Anomaly rate updated to: ${anomalyRate}`);

    res.status(200).json({
      status: 'success',
      message: 'Anomaly rate updated',
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/anomaly/reset
 * Reset anomaly increment to 0
 */
router.post('/reset', async (req, res, next) => {
  try {
    const result = await mqttService.resetAnomaly();

    logger.info('Anomaly increment reset');

    res.status(200).json({
      status: 'success',
      message: 'Anomaly increment reset to 0',
      data: result
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
