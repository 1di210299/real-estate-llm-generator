const express = require('express');
const cors = require('cors');
const { OpenAI } = require('openai');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Serve static files from current directory
app.use(express.static(__dirname));

// Load system prompt
const systemPrompt = fs.readFileSync(
    path.join(__dirname, 'docs/system_prompt.md'),
    'utf-8'
);

// Initialize OpenAI
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

app.post('/generate', async (req, res) => {
    try {
        const { leadMessage, context } = req.body;

        console.log('🤖 Generating response with streaming...');
        console.log('📝 Lead:', leadMessage.substring(0, 100));

        const startTime = Date.now();

        // Set headers for SSE
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');
        res.setHeader('X-Accel-Buffering', 'no'); // Disable nginx buffering
        res.flushHeaders(); // Send headers immediately

        const stream = await openai.chat.completions.create({
            model: 'gpt-4',
            messages: [
                { role: 'system', content: systemPrompt },
                {
                    role: 'user',
                    content: `Lead Message: ${leadMessage}\n\nContext:\n${context}\n\nGenerate a conviction-building response following the 5-step framework.`
                }
            ],
            temperature: 0.7,
            max_tokens: 600,
            stream: true
        });

        let fullResponse = '';
        let wordCount = 0;

        for await (const chunk of stream) {
            const content = chunk.choices[0]?.delta?.content || '';
            if (content) {
                fullResponse += content;
                wordCount = fullResponse.split(' ').length;
                
                // Send chunk to client
                const data = `data: ${JSON.stringify({ 
                    type: 'chunk', 
                    content,
                    wordCount 
                })}\n\n`;
                res.write(data);
                
                // Force flush to send immediately
                if (res.flush) res.flush();
                
                console.log(`📤 Sent chunk: ${content.substring(0, 30)}...`);
            }
        }

        const generationTime = ((Date.now() - startTime) / 1000).toFixed(2);
        console.log(`✅ Response generated! Words: ${wordCount}, Time: ${generationTime}s`);

        // Send final metadata
        res.write(`data: ${JSON.stringify({
            type: 'done',
            word_count: wordCount,
            generation_time: generationTime,
            timestamp: new Date().toISOString()
        })}\n\n`);

        res.end();

    } catch (error) {
        console.error('❌ Error:', error.message);
        res.write(`data: ${JSON.stringify({
            type: 'error',
            error: error.message
        })}\n\n`);
        res.end();
    }
});

app.listen(PORT, () => {
    console.log('=' .repeat(80));
    console.log(`🚀 Backend running on http://localhost:${PORT}`);
    console.log(`✅ API Key loaded: ${process.env.OPENAI_API_KEY ? 'YES' : 'NO'}`);
    console.log('=' .repeat(80));
});
