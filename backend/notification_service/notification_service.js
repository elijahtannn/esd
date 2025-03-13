const amqp = require('amqplib');
const nodemailer = require('nodemailer');
const { google } = require('googleapis');
const Mailgen = require('mailgen');
require('dotenv').config();

const EXCHANGE_NAME = 'ticketing.exchange';
const EXCHANGE_TYPE = 'topic';
const QUEUE_NAME = 'notification.queue';
const BINDING_KEYS = [
    'ticket.purchase',       // Order Service
    'ticket.transfer.*',     // Future Ticket Transfer Service
    'ticket.resale.*',       // Future Resale Service
    'ticket.refund.*'        // Refund Service
];

// OAuth2 credentials for Gmail API
const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const REDIRECT_URI = 'https://developers.google.com/oauthplayground';
const REFRESH_TOKEN = process.env.REFRESH_TOKEN;
const EMAIL_USER = process.env.EMAIL_USER;
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://localhost';

// Setup OAuth2 client for Gmail
const oAuth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);
oAuth2Client.setCredentials({ refresh_token: REFRESH_TOKEN });

// Initialize Mailgen with custom styles
const mailGenerator = new Mailgen({
    theme: 'default',
    product: {
        name: 'EVENTIVA',
        link: 'https://eventiva.com/',
        copyright: 'Copyright © 2025 EVENTIVA. All rights reserved.',
        // Add custom styles for the header
        styles: {
            // Theme specific styles
            theme: {
                link: '#2563EB',  // Change link color
                head: {
                    backgroundColor: 'white',
                    color: '#2563EB',  // Change header text color
                    fontSize: '48px',   // Make header text bigger
                    fontWeight: 'bold', // Make header text bold
                    padding: '30px',    // Add more padding
                    letterSpacing: '4px' // Add letter spacing
                }
            }
        }
    }
});

/**
 * Function to send an email.
 * @param {string} to - Recipient email.
 * @param {string} subject - Email subject.
 * @param {string} message - HTML message content.
 */
async function sendEmail(to, subject, message) {
    try {
        const accessToken = await oAuth2Client.getAccessToken();

        const transporter = nodemailer.createTransport({
            service: 'gmail',
            auth: {
                type: 'OAuth2',
                user: EMAIL_USER,
                clientId: CLIENT_ID,
                clientSecret: CLIENT_SECRET,
                refreshToken: REFRESH_TOKEN,
                accessToken: accessToken.token,
            }
        });

        const mailOptions = {
            from: `EVENTIVA <${EMAIL_USER}>`,
            to,
            subject,
            html: message,
        };

        const result = await transporter.sendMail(mailOptions);
        console.log(`✅ Email sent to ${to}`);
        return result;
    } catch (error) {
        console.error(`❌ Error sending email: ${error.message}`);
    }
}

/**
 * Function to process incoming messages and send email notifications.
 */
async function consumeMessages() {
    try {
        const connection = await amqp.connect(RABBITMQ_URL);
        const channel = await connection.createChannel();

        // Declare the exchange
        await channel.assertExchange(EXCHANGE_NAME, EXCHANGE_TYPE, { durable: true });

        // Declare queue and bind it to the exchange with all binding keys
        await channel.assertQueue(QUEUE_NAME, { durable: true });

        for (const key of BINDING_KEYS) {
            await channel.bindQueue(QUEUE_NAME, EXCHANGE_NAME, key);
        }

        console.log(`📩 Waiting for messages in queue: ${QUEUE_NAME} (Exchange: ${EXCHANGE_NAME})`);
        console.log(`🔗 Bound to routing keys: ${BINDING_KEYS.join(', ')}`);

        channel.consume(QUEUE_NAME, async (msg) => {
            if (msg !== null) {
                const eventData = JSON.parse(msg.content.toString());
                console.log('📨 Received Message:', eventData);

                const { email, eventName, ticketNumber, eventType } = eventData;

                if (eventType === 'ticket.purchase') {
                    const subject = `🎟 Your Ticket for ${eventName}`;
                    
                    // Generate email body using Mailgen
                    const emailBody = {
                        body: {
                            name: email.split('@')[0],
                            intro: `Thank you for purchasing a ticket to ${eventName}!`,
                            dictionary: {
                                'Ticket Number': ticketNumber,
                                'Event Name': eventName,
                                'Purchase Date': new Date().toLocaleDateString()
                            },
                            action: {
                                instructions: 'You can view your ticket details by clicking the button below:',
                                button: {
                                    color: '#2563EB',  // Match the blue color
                                    text: 'View Ticket',
                                    link: `https://eventiva.com/tickets/${ticketNumber}`
                                }
                            },
                            outro: 'We look forward to seeing you at the event!'
                        }
                    };

                    // Generate HTML email
                    const message = mailGenerator.generate(emailBody);

                    // Send email
                    await sendEmail(email, subject, message);
                } else {
                    console.log(`📥 Received ${eventType} message, but handling is not yet implemented.`);
                }

                // Acknowledge message after processing
                channel.ack(msg);
            }
        });
    } catch (error) {
        console.error('🚨 RabbitMQ Connection Error:', error);
    }
}

// Start the consumer
consumeMessages();
