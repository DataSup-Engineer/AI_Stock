// MongoDB Initialization Script for NASDAQ Stock Agent
// This script creates a dedicated user for the application database

db = db.getSiblingDB('nasdaq_stock_agent');

// Create application user with read/write permissions
db.createUser({
  user: process.env.MONGO_USERNAME || 'nasdaq_user',
  pwd: process.env.MONGO_PASSWORD || 'change_this_secure_user_password',
  roles: [
    {
      role: 'readWrite',
      db: 'nasdaq_stock_agent'
    }
  ]
});

// Create collections with validation
db.createCollection('stock_analyses', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['symbol', 'timestamp'],
      properties: {
        symbol: {
          bsonType: 'string',
          description: 'Stock ticker symbol - required'
        },
        timestamp: {
          bsonType: 'date',
          description: 'Analysis timestamp - required'
        },
        analysis: {
          bsonType: 'object',
          description: 'Analysis results'
        }
      }
    }
  }
});

db.createCollection('cache', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['key', 'value', 'expires_at'],
      properties: {
        key: {
          bsonType: 'string',
          description: 'Cache key - required'
        },
        value: {
          description: 'Cached value - required'
        },
        expires_at: {
          bsonType: 'date',
          description: 'Expiration timestamp - required'
        }
      }
    }
  }
});

// Create indexes for better performance
db.stock_analyses.createIndex({ symbol: 1, timestamp: -1 });
db.stock_analyses.createIndex({ timestamp: -1 });
db.cache.createIndex({ key: 1 }, { unique: true });
db.cache.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });

print('MongoDB initialization completed successfully');
