/**
 * Festora Groq Service
 * Manages communication with backend Groq endpoints and local storage.
 */
class GroqService {
  constructor() {
    this.storageKey = 'festora_groq_api_key';
  }

  getApiKey() {
    return localStorage.getItem(this.storageKey) || '';
  }

  setApiKey(key) {
    if (key) {
      localStorage.setItem(this.storageKey, key.trim());
    } else {
      localStorage.removeItem(this.storageKey);
    }
  }

  hasApiKey() {
    return !!this.getApiKey();
  }

  getHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const key = this.getApiKey();
    if (key) {
      headers['X-Groq-Api-Key'] = key;
    }
    return headers;
  }

  async testKey(key) {
    try {
      const res = await fetch('/api/groq/test-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiKey: key || this.getApiKey() })
      });
      return await res.json();
    } catch (err) {
      console.warn('Test key error:', err);
      return { valid: false, message: 'Server unreachable or offline.' };
    }
  }

  async generatePlan(params) {
    try {
      const res = await fetch('/api/groq/generate-plan', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(params)
      });
      return await res.json();
    } catch (err) {
      console.error('generatePlan error:', err);
      throw err;
    }
  }

  async chat(messages, eventContext) {
    try {
      const res = await fetch('/api/groq/chat', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ messages, eventContext })
      });
      return await res.json();
    } catch (err) {
      console.error('chat error:', err);
      return { reply: 'Could not connect to AI service. Please verify your connection or try again.', source: 'error' };
    }
  }

  async draftEmail(vendorData, eventData) {
    try {
      const res = await fetch('/api/groq/draft-email', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          vendorName: vendorData.name,
          vendorRole: vendorData.role,
          eventTitle: eventData.title,
          eventDate: eventData.date,
          budgetAlloc: `${eventData.currency || '$'}${vendorData.cost || '1,000'}`,
          notes: vendorData.notes || 'Looking for available package and services'
        })
      });
      return await res.json();
    } catch (err) {
      console.error('draftEmail error:', err);
      throw err;
    }
  }

  async rebalanceBudget(budgetItems, totalBudget) {
    try {
      const res = await fetch('/api/groq/rebalance-budget', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ budgetItems, totalBudget })
      });
      return await res.json();
    } catch (err) {
      console.error('rebalanceBudget error:', err);
      throw err;
    }
  }

  async diaryAssist(eventTitle, topic, mood) {
    try {
      const res = await fetch('/api/groq/diary-assist', {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ eventTitle, topic, mood })
      });
      return await res.json();
    } catch (err) {
      console.error('diaryAssist error:', err);
      throw err;
    }
  }
}

window.groqService = new GroqService();
