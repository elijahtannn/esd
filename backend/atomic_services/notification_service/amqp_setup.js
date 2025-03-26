const amqp = require('amqplib');
require('dotenv').config();

const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://localhost';
const EXCHANGE_NAME = 'ticketing.exchange';
const EXCHANGE_TYPE = 'topic';
const QUEUE_NAME = 'notification.queue';
const BINDING_KEYS = [
    'ticket.purchase',       
    'ticket.transfer.*',     
    'ticket.resale.*',      
    'ticket.refund.*'       
];

async function setupRabbitMQ() {
    try {
        // Connect to RabbitMQ
        console.log('🔄 Connecting to RabbitMQ...');
        const connection = await amqp.connect(RABBITMQ_URL);
        const channel = await connection.createChannel();

        // Create the exchange
        console.log(`📦 Creating exchange: ${EXCHANGE_NAME}`);
        await channel.assertExchange(EXCHANGE_NAME, EXCHANGE_TYPE, {
            durable: true
        });

        // Create the queue
        console.log(`📬 Creating queue: ${QUEUE_NAME}`);
        await channel.assertQueue(QUEUE_NAME, {
            durable: true
        });

        // Bind the queue to the exchange with all binding keys
        console.log('🔗 Setting up binding keys...');
        for (const key of BINDING_KEYS) {
            await channel.bindQueue(QUEUE_NAME, EXCHANGE_NAME, key);
            console.log(`✅ Bound ${key} to ${QUEUE_NAME}`);
        }

        console.log('✨ RabbitMQ setup completed successfully!');
        
        // Close the connection
        await channel.close();
        await connection.close();
        console.log('👋 Connection closed');
        
    } catch (error) {
        console.error('🚨 Error setting up RabbitMQ:', error);
    }
}

setupRabbitMQ();
