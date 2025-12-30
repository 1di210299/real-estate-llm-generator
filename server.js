const express = require('express');
const cors = require('cors');
const { OpenAI } = require('openai');
const fs = require('fs');
const path = require('path');
const { validateRequest, validateResponse } = require('./compliance-validator');

// Only load .env file in development (Digital Ocean uses environment variables directly)
if (process.env.NODE_ENV !== 'production') {
    require('dotenv').config({ path: path.join(__dirname, '../.env') });
}

const app = express();
const PORT = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

// Diagnostic endpoint FIRST
app.get('/health', (req, res) => {
    const indexExists = fs.existsSync(path.join(__dirname, 'index.html'));
    const docsExists = fs.existsSync(path.join(__dirname, 'docs/system_prompt.md'));
    res.json({
        status: 'ok',
        port: PORT,
        env: process.env.NODE_ENV || 'development',
        __dirname: __dirname,
        indexHtmlExists: indexExists,
        docsExists: docsExists,
        apiKeyLoaded: !!process.env.OPENAI_API_KEY
    });
});

// Test endpoint to serve HTML directly
app.get('/test', (req, res) => {
    const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf-8');
    res.setHeader('Content-Type', 'text/html');
    res.send(html);
});

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

        // STEP 1: COMPLIANCE PRE-CHECK using GPT-4 mini (fast & cheap)
        console.log('🔍 Running compliance pre-check...');
        
        const complianceCheck = await openai.chat.completions.create({
            model: 'gpt-4o-mini',
            messages: [
                {
                    role: 'system',
                    content: `You are a compliance validator for real estate communications. Only flag SEVERE violations where agent would give prohibited advice.

🚫 REJECT (Agent would need to give prohibited advice):
1. Financial Advice: "Should I pull from 401k?", "Is 6.8% return worth the risk vs savings?", "Should I take out a HELOC?"
2. Legal Opinion: "Does 'as-is' mean I can't back out?", "Is this clause enforceable?", "What are my legal rights?"
3. Fair Housing: "Families like ours", "safe for people like me", "good area for [protected class]"
4. Value Guarantees: "Will this appreciate?", "Guaranteed returns", "Can't lose money on this"

✅ ALLOW (Agent can educate without giving advice):
- Budget questions: "DTI at 42%, am I house poor?" → Can explain DTI concepts, refer to financial advisor for personal decision
- Market comparison: "City A vs City B?" → Can compare market data, let buyer decide
- Investment concepts: "What's a realistic cap rate?" → Can explain cap rates as concept, provide market ranges
- Down payment: "$40K saved, should I wait?" → Can explain down payment options, pros/cons of each
- School districts: "Houses near good schools are $350K+" → Can discuss market pricing, school ratings are public data
- General concerns: "Is now good time given 7% rates?" → Can discuss market conditions without predicting or recommending

CRITICAL: "families like ours/us/yours" = ALWAYS VIOLATION (Fair Housing)
CRITICAL: Contract interpretation = ALWAYS VIOLATION (Legal Opinion)  
CRITICAL: 401k/retirement account advice = ALWAYS VIOLATION (Financial Advice)

Respond ONLY "COMPLIANT" or "VIOLATION: [type] - [one line reason]"`
                },
                {
                    role: 'user',
                    content: `Lead Message: "${leadMessage}"\n\nContext: "${context || 'None provided'}"\n\nIs this compliant?`
                }
            ],
            temperature: 0,
            max_tokens: 200
        });

        const complianceResult = complianceCheck.choices[0].message.content.trim();
        console.log('📋 Compliance check result:', complianceResult);

        // If violation detected, refuse immediately
        if (complianceResult.toUpperCase().startsWith('VIOLATION')) {
            console.log('🛑 COMPLIANCE VIOLATION DETECTED');
            res.setHeader('Content-Type', 'text/event-stream');
            res.setHeader('Cache-Control', 'no-cache');
            res.setHeader('Connection', 'keep-alive');
            res.flushHeaders();
            
            // Extract the redirect message from the compliance check
            const redirectMessage = complianceResult.split('\n').slice(1).join('\n').trim() || 
                "I cannot provide this type of advice. Please consult with a licensed professional who can review your specific situation.";
            
            res.write(`data: ${JSON.stringify({
                type: 'error',
                error: redirectMessage,
                severity: 'COMPLIANCE_VIOLATION'
            })}\n\n`);
            
            res.end();
            return;
        }

        console.log('✅ Compliance check passed, proceeding with generation...');

        // STEP 2: Generate main response with full system prompt

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
            }
        }

        const generationTime = ((Date.now() - startTime) / 1000).toFixed(2);
        console.log(`✅ Response generated! Words: ${wordCount}, Time: ${generationTime}s`);

        // COMPLIANCE VALIDATION - Check response after generation
        const responseValidation = validateResponse(fullResponse);
        
        if (!responseValidation.valid) {
            console.log('⚠️  RESPONSE VIOLATIONS:', responseValidation.violations);
            
            // Send warning but still deliver response
            res.write(`data: ${JSON.stringify({
                type: 'warning',
                message: 'This response may contain compliance issues. Please review carefully before sending.',
                violations: responseValidation.violations
            })}\n\n`);
        }

        // Send final metadata
        res.write(`data: ${JSON.stringify({
            type: 'done',
            word_count: wordCount,
            generation_time: generationTime,
            timestamp: new Date().toISOString(),
            compliance_warnings: responseValidation.warnings || []
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

// Serve static files AFTER API routes
app.use(express.static(__dirname));

// Fallback to index.html for any other route (SPA behavior)
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
    console.log('=' .repeat(80));
    console.log(`🚀 Backend running on port ${PORT}`);
    console.log(`✅ API Key loaded: ${process.env.OPENAI_API_KEY ? 'YES' : 'NO'}`);
    console.log(`🌐 Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log('=' .repeat(80));
});
