const express = require('express');
const cors = require('cors');
const config = require('./config/config');
const logger = require('./utils/logger');
const mqttService = require('./services/mqtt.service');
const anomalyRoutes = require('./routes/anomaly.routes');
const simulatorRoutes = require('./routes/simulator.routes');
const healthRoutes = require('./routes/health.routes');
const { errorHandler, notFound } = require('./middleware/error');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`);
  next();
});

// Routes
app.use('/health', healthRoutes);
app.use('/api/anomaly', anomalyRoutes);
app.use('/api/simulator', simulatorRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'Sensor Simulator Control API',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      health: '/health',
      simulator: {
        start: 'POST /api/simulator/start',
        stop: 'POST /api/simulator/stop',
        status: 'GET /api/simulator/status',
        config: 'GET /api/simulator/config'
      },
      anomaly: {
        start: 'POST /api/anomaly/start',
        stop: 'POST /api/anomaly/stop',
        status: 'GET /api/anomaly/status',
        updateRate: 'PATCH /api/anomaly/rate',
        reset: 'POST /api/anomaly/reset'
      }
    }
  });
});

// Error handling
app.use(notFound);
app.use(errorHandler);

// Initialize and start server
async function start() {
  try {
    // Connect to MQTT broker
    await mqttService.connect();
    logger.info('MQTT service initialized');

    // Start Express server
    app.listen(config.server.port, () => {
      logger.info(`Server running on port ${config.server.port}`);
      logger.info(`Environment: ${config.server.env}`);
      logger.info(`MQTT Broker: ${config.mqtt.brokerHost}:${config.mqtt.brokerPort}`);
      logger.info(`Control Topic: ${config.mqtt.controlTopic}`);
    });
  } catch (error) {
    logger.error(`Failed to start server: ${error.message}`);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  mqttService.disconnect();
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  mqttService.disconnect();
  process.exit(0);
});

// Start the application
start();
