const amqp = require('amqplib');

async function publishMessage() {
    const connection = await amqp.connect('amqp://localhost');
    const channel = await connection.createChannel();
    
    const exchange = 'ticketing.exchange';
    const routingKey = 'ticket.purchase'; 
    
    await channel.assertExchange(exchange, 'topic', { durable: true });

    const message = {
        email: 'elijahsyzf@hotmail.com',
        eventName: 'Music Concert',
        ticketNumber: 'TCKT12345',
        eventType: 'ticket.purchase'
    };

    channel.publish(exchange, routingKey, Buffer.from(JSON.stringify(message)));
    console.log('✅ Message Published:', message);

    setTimeout(() => {
        connection.close();
    }, 500);
}

publishMessage();
