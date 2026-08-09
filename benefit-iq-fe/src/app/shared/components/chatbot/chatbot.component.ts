import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatbotService, ChatMessage } from '../../services/chatbot.service';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="chatbot-wrapper">
      <!-- Floating Trigger Button -->
      <button class="chatbot-trigger" (click)="toggleOpen()" [class.active]="isOpen()">
        <svg *ngIf="!isOpen()" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <svg *ngIf="isOpen()" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>

      <!-- Chat Window Panel -->
      <div *ngIf="isOpen()" class="chatbot-window card">
        <div class="chatbot-header">
          <div class="chatbot-header-title">
            <span class="status-dot"></span>
            <strong>Benefit IQ AI Assistant</strong>
          </div>
          <div class="chatbot-header-actions">
            <button class="btn-text" (click)="clearChat()" title="Clear Chat">Clear</button>
          </div>
        </div>

        <div class="chatbot-messages">
          <div *ngFor="let msg of messages()" class="chat-bubble" [class.user]="msg.sender === 'user'" [class.assistant]="msg.sender === 'assistant'">
            <div class="chat-text">{{ msg.text }}</div>
            <div class="chat-time">{{ msg.timestamp | date:'shortTime' }}</div>
          </div>

          <div *ngIf="isTyping()" class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>

        <!-- Prompt Suggestions -->
        <div class="chatbot-prompts">
          <button *ngFor="let prompt of promptSuggestions" (click)="sendPrompt(prompt)" class="chip-btn">
            {{ prompt }}
          </button>
        </div>

        <!-- Message Input -->
        <div class="chatbot-input-bar">
          <input
            type="text"
            class="input-field"
            [(ngModel)]="userInput"
            (keyup.enter)="sendMessage()"
            placeholder="Ask AI about benefits, claims, deductible..."
          />
          <button class="btn-primary" (click)="sendMessage()" [disabled]="!userInput.trim()">Send</button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .chatbot-wrapper {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      z-index: 9999;
    }
    .chatbot-trigger {
      width: 3.5rem;
      height: 3.5rem;
      border-radius: 50%;
      background: var(--gradient-primary);
      color: white;
      border: none;
      box-shadow: var(--shadow-lg);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: transform var(--transition-fast);
    }
    .chatbot-trigger:hover {
      transform: scale(1.05);
    }
    .chatbot-window {
      position: absolute;
      bottom: 4.5rem;
      right: 0;
      width: 380px;
      max-width: calc(100vw - 2rem);
      height: 520px;
      display: flex;
      flex-direction: column;
      padding: 0 !important;
      overflow: hidden;
      box-shadow: var(--shadow-xl);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-xl);
    }
    .chatbot-header {
      padding: var(--space-md);
      background: var(--color-surface-elevated);
      border-bottom: 1px solid var(--color-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .status-dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--color-success);
      margin-right: 8px;
    }
    .chatbot-messages {
      flex: 1;
      padding: var(--space-md);
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: var(--space-sm);
    }
    .chat-bubble {
      max-width: 80%;
      padding: 0.75rem 1rem;
      border-radius: var(--radius-lg);
      font-size: var(--font-sm);
    }
    .chat-bubble.user {
      align-self: flex-end;
      background: var(--color-primary);
      color: white;
      border-bottom-right-radius: 2px;
    }
    .chat-bubble.assistant {
      align-self: flex-start;
      background: var(--color-surface-hover);
      color: var(--color-text);
      border-bottom-left-radius: 2px;
    }
    .chat-time {
      font-size: 10px;
      opacity: 0.7;
      margin-top: 4px;
      text-align: right;
    }
    .typing-indicator {
      display: flex;
      gap: 4px;
      padding: 8px 12px;
      background: var(--color-surface-hover);
      border-radius: var(--radius-lg);
      width: fit-content;
    }
    .typing-indicator span {
      width: 6px;
      height: 6px;
      background: var(--color-text-tertiary);
      border-radius: 50%;
      animation: bounce 1.2s infinite ease-in-out;
    }
    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
    .chatbot-prompts {
      display: flex;
      gap: 6px;
      padding: 6px var(--space-md);
      overflow-x: auto;
      background: var(--color-surface-elevated);
      border-top: 1px solid var(--color-border-subtle);
    }
    .chip-btn {
      font-size: var(--font-xs);
      padding: 4px 10px;
      background: var(--color-surface-hover);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-full);
      white-space: nowrap;
      cursor: pointer;
    }
    .chatbot-input-bar {
      display: flex;
      gap: 8px;
      padding: var(--space-md);
      border-top: 1px solid var(--color-border);
      background: var(--color-surface);
    }
    .input-field {
      flex: 1;
      padding: 0.5rem 0.75rem;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      font-size: var(--font-sm);
    }
    @keyframes bounce {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }
  `]
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
