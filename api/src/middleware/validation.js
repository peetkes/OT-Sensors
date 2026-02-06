const Joi = require('joi');

const schemas = {
  startAnomaly: Joi.object({
    anomalyRate: Joi.number().min(0).max(10).default(0.1),
    sensors: Joi.array().items(Joi.string()).optional(),
    enabled: Joi.boolean().default(true)
  }),

  updateRate: Joi.object({
    anomalyRate: Joi.number().min(0).max(10).required()
  }),

  simulatorControl: Joi.object({
    production_lines: Joi.array()
      .items(Joi.string().pattern(/^LINE_\d{3}$/))
      .min(1)
      .required()
      .messages({
        'array.min': 'At least one production line ID required',
        'string.pattern.base': 'Production line ID must match format LINE_XXX (e.g., LINE_001)'
      })
  })
};

const validate = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body, {
      abortEarly: false,
      stripUnknown: true
    });

    if (error) {
      const errors = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }));

      return res.status(400).json({
        status: 'error',
        message: 'Validation failed',
        errors
      });
    }

    req.validatedBody = value;
    next();
  };
};

module.exports = {
  schemas,
  validate
};
