
const axios = require('axios');

async function fetchNewsletterContent() {
  try {
    console.log('DATA_API_KEY present:', !!process.env.DATA_API_KEY);
    const response = await axios.get('https://api.api-ninjas.com/v1/factoftheday', {
      headers: {
        'X-Api-Key': process.env.DATA_API_KEY
      }
    });
    console.log('fetchNewsletterContent: status', response.status, 'data:', response.data);
    // Handle API returning either an array or an object
    if (Array.isArray(response.data) && response.data.length > 0) {
      return response.data.map(f => f.fact);
    }
    if (response.data && response.data.fact) {
      return [response.data.fact];
    }
    return [];
  } catch (error) {
    console.error('Error fetching newsletter content:', error.response ? error.response.data : error.message);
    return [];
  }
}

module.exports = fetchNewsletterContent;
