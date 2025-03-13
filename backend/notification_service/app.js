const nodemailer = require("nodemailer")
const {google} = require("googleapis")

const CLIENT_ID = "603980424659-jiqs010nggvjmn6ve8c243nfral3q5a7.apps.googleusercontent.com"
const CLIENT_SECRET = "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"
const REDIRECT_URI = "https://developers.google.com/oauthplayground"
const REFRESH_TOKEN = "1//044Taxb73UAEsCgYIARAAGAQSNwF-L9Irgephz0kPH0GLvIejgaQjJxeXYiB8BTFoNMlpnWHQKYHm512gcDx_4aOpgT9A1fiDrDA"

const oAuth2Client = new google.auth.OAuth2(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
oAuth2Client.setCredentials({refresh_token: REFRESH_TOKEN})

async function sendMail(){
    try{
        const accessToken = await oAuth2Client.getAccessToken()
        const transport = nodemailer.createTransport({
            service: "gmail",
            auth: {
                type: 'OAuth2',
                user: 'elijahjcas@gmail.com',
                clientId: CLIENT_ID,
                clientSecret: CLIENT_SECRET,
                refreshToken: REFRESH_TOKEN,
                accessToken: accessToken
            }
        })
        const mailOptions = {
            from: 'EVENTIVA <elijahjcas@gmail.com>',
            to: 'elijah.tan.2023@smu.edu.sg',
            subject: 'Ticket Confirmation',
            text: 'This is a test email',
            html: '<h1>Hello World</h1>',
        };

        const result = await transport.sendMail(mailOptions)
        return result

    }catch(error){
        return error
    }
}

sendMail().then(result=> console.log('Email sent...', result))
.catch(error=> console.log('Error sending email', error))
