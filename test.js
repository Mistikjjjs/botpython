const express = require('express');
const puppeteer = require('puppeteer');
const app = express();
const port = 3000;
app.get('/send-message', async (req, res) => {
    const { message } = req.query; // Obtén el mensaje de los parámetros de la URL
    if (!message) {
        return res.status(400).json({ error: 'Message is required as a query parameter' });
    }
    try {
        const browser = await puppeteer.launch({ headless: true });
        const page = await browser.newPage();
        // Navega a la página
        await page.goto('https://uncensored.chat/c/new', { waitUntil: 'networkidle2' });
        // Espera a que el campo de texto esté disponible
        await page.waitForSelector('textarea[name="search"]');
        // Escribe el mensaje en el campo de texto
        await page.type('textarea[name="search"]', message);
        // Haz clic en el botón de enviar
        await page.click('button[type="submit"]');
        // Espera a que la respuesta esté disponible
        await page.waitForSelector('#chat-container div:last-child');
        // Obtén el texto de la última respuesta
        const response = await page.evaluate(() => {
            const chatContainer = document.querySelector('#chat-container');
            const lastMessage = chatContainer.lastElementChild;
            return lastMessage ? lastMessage.innerText : null;
        });
        await browser.close();
        res.json({ response });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'An error occurred while processing your request' });
    }
});
app.listen(port, () => {
    console.log(`API running at http://localhost:${port}`);
});
