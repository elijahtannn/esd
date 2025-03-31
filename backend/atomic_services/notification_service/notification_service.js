const amqp = require('amqplib');
const nodemailer = require('nodemailer');
const { google } = require('googleapis');
const Mailgen = require('mailgen');
const axios = require('axios');
require('dotenv').config();

const EXCHANGE_NAME = 'ticketing.exchange';
const EXCHANGE_TYPE = 'topic';
const QUEUE_NAME = 'notification.queue';
const BINDING_KEYS = [
    'ticket.purchase',       
    'ticket.transfer.*',     
    'ticket.resale.*',       
    'ticket.refund.*'        
];

// OAuth2 credentials for Gmail API
const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const REDIRECT_URI = 'https://developers.google.com/oauthplayground';
const REFRESH_TOKEN = process.env.REFRESH_TOKEN;
const EMAIL_USER = process.env.EMAIL_USER;
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://guest:guest@rabbitmq:5672';
// Change this line in notification_service.js
const USER_SERVICE_URL = process.env.USER_SERVICE_URL || 'http://localhost:5003';

// Setup OAuth2 client for Gmail
const oAuth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI);
oAuth2Client.setCredentials({ refresh_token: REFRESH_TOKEN });

// Initialize Mailgen with custom styles
const mailGenerator = new Mailgen({
    theme: 'default',
    product: {
        name: 'EVENTIVA',
        link: 'http://localhost:5173',
        copyright: 'Copyright © 2025 EVENTIVA. All rights reserved.',
        // Add custom styles for the header
        styles: {
            theme: {
                link: '#2563EB',
                head: {
                    backgroundColor: 'white',
                    color: '#2563EB',  
                    fontSize: '48px',   
                    fontWeight: 'bold', 
                    padding: '30px',    
                    letterSpacing: '4px' 
                }
            }
        }
    }
});

// Add frontend URL constant at the top with other constants
const FRONTEND_URL = 'http://localhost:5173';

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
 * Function to fetch users interested in a specific event
 * @param {string} eventId - The event ID to look up
 * @returns {Array} - Array of users interested in the event
 */
async function getInterestedUsers(eventId) {
    try {
        const response = await axios.get(`${USER_SERVICE_URL}/events/${eventId}/interested-users`);
        return response.data.users || [];
    } catch (error) {
        console.error(`Error fetching interested users for event ${eventId}: ${error.message}`);
        return [];
    }
}

/**
 * Function to send resale availability notifications to interested users
 * @param {string} eventId - The event ID with available resale tickets
 * @param {object} eventDetails - Details about the event
 */
async function sendResaleNotifications(eventId, eventDetails) {
    try {
        const interestedUsers = await getInterestedUsers(eventId);
        console.log(`📧 Sending resale notifications to ${interestedUsers.length} users for event ${eventId}`);
        
        if (interestedUsers.length === 0) {
            console.log(`ℹ️ No users are interested in resale tickets for event ${eventId}`);
            return;
        }
        
        const { 
            eventName, 
            ticketPrice, 
            ticketQuantity, 
            eventDate, 
            eventLocation,
            eventVenue,
            categoryName
          } = eventDetails;
        
        for (const user of interestedUsers) {
            const subject = `🎟 Resale Tickets Available for ${eventName}`;
            
            // Generate email body using Mailgen
            const emailBody = {
                body: {
                    name: user.name || user.email.split('@')[0],
                    intro: `Great news! Resale tickets are now available for ${eventName}.`,
                    dictionary: {
                        'Event': eventName,
                        'Date': eventDate || 'See event details',
                        'Location': eventLocation || 'See event details',
                        'Available Tickets': ticketQuantity || 'Limited quantity',
                        'Price': ticketPrice ? `$${ticketPrice}` : 'See event details'
                    },
                    action: {
                        instructions: 'Act quickly! Resale tickets are typically sold on a first-come, first-served basis.',
                        button: {
                            color: '#2563EB',
                            text: 'Buy Tickets Now',
                            link: `${FRONTEND_URL}/events/${eventId}`
                        }
                    },
                    outro: 'If you no longer wish to receive resale notifications for this event, you can unsubscribe from your profile page.'
                }
            };

            // Generate HTML email
            const message = mailGenerator.generate(emailBody);

            // Send email
            await sendEmail(user.email, subject, message);
        }
        
        console.log(`Resale notifications sent to all interested users for event ${eventId}`);
    } catch (error) {
        console.error(`Error sending resale notifications: ${error.message}`);
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

                const { email, eventName, ticketNumber, eventType, sender_email, recipient_email, role, amount, message, eventId } = eventData;

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
                                    color: '#2563EB',
                                    text: 'View Ticket',
                                    link: `${FRONTEND_URL}/profile`
                                }
                            },
                            outro: 'We look forward to seeing you at the event!'
                        }
                    };

                    // Generate HTML email
                    const message = mailGenerator.generate(emailBody);

                    // Send email
                    await sendEmail(email, subject, message);
                } else if (eventType === 'ticket.transfer.pending') {
                    const subject = `🎟 Pending Ticket Transfer for ${eventName}`;
                    
                    // Generate email body using Mailgen
                    const emailBody = {
                        body: {
                            name: email.split('@')[0],
                            intro: `You have a pending ticket transfer from ${sender_email} for ${eventName}!`,
                            dictionary: {
                                'Ticket Number': ticketNumber,
                                'Event Name': eventName,
                                'From': sender_email
                            },
                            action: {
                                instructions: 'You can view and accept the transfer by clicking the button below:',
                                button: {
                                    color: '#2563EB',
                                    text: 'View Transfer',
                                    link: `${FRONTEND_URL}/profile`
                                }
                            },
                            outro: 'This transfer will expire in 24 hours if not accepted.'
                        }
                    };

                    // Generate HTML email
                    const message = mailGenerator.generate(emailBody);

                    // Send email
                    await sendEmail(email, subject, message);
                } else if (eventType === 'ticket.transfer.success') {
                    const subject = `🎟 Ticket Transfer ${role === 'sender' ? 'Completed' : 'Received'} for ${eventName}`;
                    
                    const emailBody = {
                        body: {
                            name: email.split('@')[0],
                            intro: role === 'sender' 
                                ? `Your ticket for ${eventName} has been successfully transferred to ${recipient_email}!`
                                : `The ticket transfer from ${sender_email} for ${eventName} has been completed!`,
                            dictionary: {
                                'Ticket Number': ticketNumber,
                                'Event Name': eventName,
                                [role === 'sender' ? 'Transferred To' : 'Transferred From']: 
                                    role === 'sender' ? recipient_email : sender_email,
                                'Transfer Date': new Date().toLocaleDateString()
                            },
                            action: {
                                instructions: 'You can view your tickets by clicking the button below:',
                                button: {
                                    color: '#2563EB',
                                    text: 'View Tickets',
                                    link: `${FRONTEND_URL}/profile`
                                }
                            },
                            outro: role === 'sender' 
                                ? 'Thank you for using our transfer service!'
                                : 'Enjoy the event!'
                        }
                    };

                    // Generate HTML email
                    const message = mailGenerator.generate(emailBody);

                    // Send email
                    await sendEmail(email, subject, message);
                } else if (eventType === 'ticket.refund.complete') {
                    const subject = `💰 Refund Processed for ${eventName || "Ticket Refund"}`;
                    
                    // Generate email body using Mailgen
                    const emailBody = {
                        body: {
                            name: email.split('@')[0],
                            intro: message || `Your refund has been processed successfully!`,
                            dictionary: {
                                'Ticket Number': ticketNumber,
                                'Refund Amount': `$${amount}`,
                                'Refund Date': new Date().toLocaleDateString()
                            },
                            action: {
                                instructions: 'You can view your tickets and transactions by clicking the button below:',
                                button: {
                                    color: '#2563EB',
                                    text: 'View Account',
                                    link: `${FRONTEND_URL}/profile`
                                }
                            },
                            outro: 'Thank you for using our service!'
                        }
                    };
                
                    // Generate HTML email
                    const emailMessage = mailGenerator.generate(emailBody);
                
                    // Send email
                    await sendEmail(email, subject, emailMessage);
                    console.log(`Refund notification email sent to ${email}`);
                } else if (eventType === 'ticket.resale.available') {
                    // This handles resale tickets becoming available
                    // The event data should include details about the resale
                    console.log(`🎫 Resale tickets available for event ID: ${eventId || eventData.eventId}`);
                    
                    // Extract the event ID
                    const resaleEventId = eventId || eventData.eventId;
                    
                    if (!resaleEventId) {
                        console.error('No event ID provided for resale notification');
                        channel.ack(msg);
                        return;
                    }

                    const eventDetails = {
                        eventId: resaleEventId,
                        eventName: eventData.eventName || eventData.Name,
                        eventLocation: eventData.eventLocation || eventData.Venue,
                        eventVenue: eventData.eventVenue || eventData.Venue,
                        ticketPrice: eventData.ticketPrice,
                        ticketQuantity: eventData.ticketQuantity || eventData.AvailableTickets,
                        eventDate: eventData.eventDate || eventData.Date,
                        categoryName: eventData.categoryName || eventData.Category
                    };
                    
                    // Send notifications to all interested users
                    await sendResaleNotifications(resaleEventId, eventDetails);
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