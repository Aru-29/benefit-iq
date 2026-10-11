import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatbotService, ChatMessage } from '../../services/chatbot.service';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chatbot.component.html',
  styleUrl: './chatbot.component.css'
})
export class ChatbotComponent {
  private readonly chatbotService = inject(ChatbotService);

  isOpen = signal(false);
  isTyping = signal(false);
  userInput = '';

  messages = signal<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Hello! I am your Benefit IQ AI assistant. How can I help you with your benefits, claims, or coverage today?',
      timestamp: new Date(),
    }
  ]);

  promptSuggestions = [
    'How do I submit a claim?',
    'What is my deductible status?',
    'View active benefit plans'
  ];

  toggleOpen() {
    this.isOpen.set(!this.isOpen());
  }

  sendPrompt(prompt: string) {
    this.userInput = prompt;
    this.sendMessage();
  }

  sendMessage() {
    const text = this.userInput.trim();
    if (!text) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date()
    };

    this.messages.set([...this.messages(), userMsg]);
    this.userInput = '';
    this.isTyping.set(true);

    this.chatbotService.sendMessage(text).subscribe({
      next: (assistantMsg) => {
        this.isTyping.set(false);
        this.messages.set([...this.messages(), assistantMsg]);
      },
      error: () => this.isTyping.set(false)
    });
  }

  clearChat() {
    this.messages.set([]);
  }
}
