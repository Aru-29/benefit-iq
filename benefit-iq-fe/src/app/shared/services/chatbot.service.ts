import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { delay } from 'rxjs/operators';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

@Injectable({
  providedIn: 'root',
})
export class ChatbotService {
  private readonly defaultResponses: Record<string, string> = {
    claim: 'To submit a new claim, navigate to your Benefits Dashboard and click on "Submit Claim". Ensure you upload itemized receipts and provider notes.',
    deductible: 'Your current Year-To-Date deductible is $450 / $1,500 met. Out-of-pocket maximum is $1,200 / $5,000.',
    plans: 'You are currently enrolled in the Premier PPO Health Plan, Comprehensive Dental, and Executive Vision Plan.',
    help: 'I can assist you with benefit utilization inquiries, claim submission guidance, deductible status checks, and plan coverage details.',
  };

  sendMessage(userMessage: string): Observable<ChatMessage> {
    const textLower = userMessage.toLowerCase();
    let reply = 'I am your Benefit IQ AI Assistant. How can I help you manage your healthcare benefits today?';

    if (textLower.includes('claim')) {
      reply = this.defaultResponses['claim'];
    } else if (textLower.includes('deductible') || textLower.includes('cost') || textLower.includes('limit')) {
      reply = this.defaultResponses['deductible'];
    } else if (textLower.includes('plan') || textLower.includes('coverage') || textLower.includes('enrolled')) {
      reply = this.defaultResponses['plans'];
    } else if (textLower.includes('help') || textLower.includes('hello') || textLower.includes('hi')) {
      reply = this.defaultResponses['help'];
    } else {
      reply = `Thank you for your inquiry regarding "${userMessage}". Benefit IQ AI is analyzing your account status. Your coverage is active and fully compliant.`;
    }

    const assistantMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'assistant',
      text: reply,
      timestamp: new Date(),
    };

    return of(assistantMsg).pipe(delay(800));
  }
}
