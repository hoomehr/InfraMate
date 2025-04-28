const serverless = require('serverless-http');
const app = require('./index');

// Create serverless handler for AWS Lambda
module.exports.handler = serverless(app); 