const express=require('express');
const mongoose=require('mongoose');
const dotenv = require('dotenv');
const { Resend } = require('resend');
const cron = require('node-cron');
const path = require('path');
const fetchNewsletterContent = require('./fetchNewsletterContent');
dotenv.config();

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

mongoose.connect(process.env.MONGO_DB_CONNECTION_STRING, {
    dbName:'chintu_emaildb'
});

const subscriberSchema = new mongoose.Schema({
    name: String,
    email: String
});
const Subscriber = mongoose.model('Subscriber', subscriberSchema);


const resend = new Resend(process.env.RESEND_API_KEY);

app.post('/subscribe', async (req, res) => {
    const { name, email } = req.body;
    if (!name || !email) {
        return res.status(400).send('Name and email are required');
    }
    try {
        const existing = await Subscriber.findOne({ email });
        if (!existing) {
        await Subscriber.create({ name, email });
        }
        await resend.emails.send({
            from: "onboarding@resend.dev",
            to: email,
            subject: 'Welcome to our Newsletter!',
            html: `<p>Hiii <b>${name}</b> :),</p>
<p><b>Welcome to Chintu's!</b></p>
<p><b>Thank you for subscribing to our Newsletter Service!</b></p>
<p>From today onwards, you will receive our emails <b>every Sunday</b>.<br>
The emails will be curated especially for you on the <b>basis</b> of what you search on Chintu and your <b>preferred field of knowledge</b>.</p>
<p>Hope you like the emails and keep supporting <b><span style="color:#023430">CHINTU</span></b>.</p>
<p>For any queries you can reach out to us on this email. We'll be more than happy to assist you.</p>
<br>
<p>Yours Truly,<br>Team Chintu</p>`
        });
        res.sendFile(path.join(__dirname, 'subscribed.html'));
    } catch (err) {
        console.error(err);
        res.status(500).send('Error subscribing');
    }
});

cron.schedule('0 12 * * 0', async () => {
    try {
        const subscribers = await Subscriber.find();
        const facts = await fetchNewsletterContent();
        let factsHtml = '';
        if (facts.length > 0) {
            factsHtml = '<h3>Interesting Facts of the Week:</h3><ul>' + facts.map(f => `<li>${f}</li>`).join('') + '</ul>';
        } else {
            factsHtml = '<p>No facts available this week.</p>';
        }
        for (const sub of subscribers) {
            await resend.emails.send({
                from: "onboarding@resend.dev",
                to: sub.email,
                subject: 'Your Weekly Newsletter',
                html: `<p>Hiii <b>${sub.name}</b> :),</p>\n${factsHtml}\n<p>Thank you for subscribing to our Newsletter Service!</p>\n<p>Hope you like the emails and keep supporting <b><span style=\"color:#023430\">CHINTU</span></b>.</p>\n<p>For any queries you can reach out to us on this email. We'll be more than happy to assist you.</p>\n<br>\n<p>Yours Truly,<br>Team Chintu</p>`
            });
        }
        console.log('Weekly emails sent');
    } catch (err) {
        console.error('Error in scheduled newsletter job:', err);
    }
}, {
    timezone: 'Asia/Kolkata'
});

const PORT = 3000;
app.listen(PORT, () => {
    console.log('server is running');
});