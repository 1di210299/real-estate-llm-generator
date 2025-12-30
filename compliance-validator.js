// Compliance Validation Module
// Validates requests and responses against guardrails framework

const HARD_STOPS = {
    financial_advice: {
        keywords: [
            '401k', 'retirement', 'investment return', 'roi calculation', 'cap rate',
            'tax strategy', 'debt management', 'should i invest', 'cash flow projection',
            'pull from retirement', 'max out', 'pay off loan', 'financial product'
        ],
        message: "I cannot provide financial advice. I recommend speaking with a licensed financial advisor who can review your complete financial picture. I can help you with property search, market data, and the home buying process."
    },
    
    legal_opinion: {
        keywords: [
            'contract clause', 'legal right', 'what does this mean legally', 'can they legally',
            'breach of contract', 'sue', 'lawsuit', 'attorney review', 'legal interpretation',
            'what are my rights', 'legally enforce', 'legal obligation', 'terminate contract'
        ],
        message: "That's a question for a licensed real estate attorney. I can help you understand the general process and connect you with legal professionals, but I cannot provide legal advice or interpret contracts."
    },
    
    fair_housing: {
        keywords: [
            'people like me', 'people like us', 'safe neighborhood', 'good families', 
            'families like', 'demographics', 'racial composition', 'religious community', 
            'avoid areas', 'bad neighborhood', 'where should i not look', 'type of people', 
            'family oriented area', 'you know what i mean', 'mostly families',
            'protected class', 'good schools and', 'safe areas', 'certain type'
        ],
        message: "I can provide objective data on schools, crime statistics, amenities, and commute times. I'd love to understand what specific features matter to you - like proximity to work, home size, specific amenities - and I'll show you all neighborhoods that match those criteria."
    },
    
    value_guarantees: {
        keywords: [
            'guaranteed appreciation', 'definitely increase', 'cant lose value',
            'will appreciate', 'guaranteed return', 'promise value', 'will be worth',
            'guaranteed rent', 'always goes up', 'cant go down'
        ],
        message: "While I can show you historical trends and market data, no one can guarantee future property values or rental income. I can help you understand market conditions, comparable sales, and neighborhood trends so you can make an informed decision."
    },
    
    medical_safety: {
        keywords: [
            'medical condition', 'disability accommodation', 'health concern',
            'mold safe', 'air quality health', 'safe for condition', 'wheelchair',
            'medical needs', 'health risk'
        ],
        message: "I recommend having a professional inspector evaluate any health or safety concerns. I can share what the disclosures say and connect you with specialists who can properly assess this."
    },
    
    financing_terms: {
        keywords: [
            'what interest rate', 'guaranteed approval', 'loan qualification',
            'exact payment', 'monthly payment calculation', 'interest rate quote',
            'can i qualify', 'lender will approve', 'guaranteed financing'
        ],
        message: "For specific rates, loan terms, and qualification questions, you'll need to speak with a licensed lender. I can provide general market ranges and connect you with trusted lenders if you need referrals."
    }
};

const SOFT_GUARDRAILS = {
    market_predictions: {
        keywords: ['market will', 'prices will', 'market prediction', 'future market', 'will appreciate'],
        disclaimer: "Based on historical data and current trends, [observation]. However, market conditions can change, and past performance doesn't guarantee future results."
    },
    
    property_condition: {
        keywords: ['looks like', 'appears to', 'seems to be', 'condition of', 'needs repair'],
        disclaimer: "Based on what's visible or disclosed, [observation]. I strongly recommend a professional home inspection to fully evaluate the property's condition."
    },
    
    timeline_estimates: {
        keywords: ['how long', 'timeline', 'when will', 'closing date', 'days to close'],
        disclaimer: "Typically this takes [timeframe], but it can vary based on financing, inspections, title work, and other factors. Several variables are outside our control."
    }
};

function validateRequest(leadMessage, context) {
    const combinedText = `${leadMessage} ${context}`.toLowerCase();
    
    // Check for hard stops
    for (const [violation, config] of Object.entries(HARD_STOPS)) {
        for (const keyword of config.keywords) {
            if (combinedText.includes(keyword.toLowerCase())) {
                return {
                    valid: false,
                    violation: violation,
                    message: config.message,
                    severity: 'HARD_STOP'
                };
            }
        }
    }
    
    // Check for soft guardrails (warnings, but allow to proceed)
    const warnings = [];
    for (const [category, config] of Object.entries(SOFT_GUARDRAILS)) {
        for (const keyword of config.keywords) {
            if (combinedText.includes(keyword.toLowerCase())) {
                warnings.push({
                    category: category,
                    disclaimer: config.disclaimer
                });
                break; // Only add one warning per category
            }
        }
    }
    
    return {
        valid: true,
        warnings: warnings,
        severity: warnings.length > 0 ? 'SOFT_WARNING' : 'CLEAN'
    };
}

function validateResponse(responseText) {
    const lowerResponse = responseText.toLowerCase();
    const violations = [];
    
    // Check for prohibited language in responses
    const prohibitedPhrases = [
        'you should invest',
        'guaranteed return',
        'definitely appreciate',
        'you should pull from',
        'this is legal',
        'your legal right',
        'you can sue',
        'safe neighborhood for',
        'good area for families like',
        'i guarantee',
        'you will definitely',
        'cant lose',
        'always goes up'
    ];
    
    for (const phrase of prohibitedPhrases) {
        if (lowerResponse.includes(phrase)) {
            violations.push({
                phrase: phrase,
                severity: 'HIGH',
                message: 'Response contains prohibited advisory language'
            });
        }
    }
    
    // Check for missing disclaimers when discussing predictions
    const needsDisclaimer = [
        'market will',
        'prices will',
        'value will increase',
        'will appreciate'
    ];
    
    for (const phrase of needsDisclaimer) {
        if (lowerResponse.includes(phrase) && !lowerResponse.includes('however') && !lowerResponse.includes('past performance')) {
            violations.push({
                phrase: phrase,
                severity: 'MEDIUM',
                message: 'Market prediction without proper disclaimer'
            });
        }
    }
    
    return {
        valid: violations.length === 0,
        violations: violations
    };
}

module.exports = {
    validateRequest,
    validateResponse,
    HARD_STOPS,
    SOFT_GUARDRAILS
};
